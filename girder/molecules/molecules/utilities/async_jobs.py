import json
import requests
import sys
import traceback

from requests_futures.sessions import FuturesSession

from girder import events
from girder.constants import TerminalColor
from girder.models.model_base import ValidationException
from girder.models.setting import Setting

from girder_jobs.models.job import Job
from girder_jobs.constants import JobStatus

from .whitelist_cjson import whitelist_cjson

from molecules.constants import PluginSettings

from .. import avogadro
from .. import openbabel
from .. import semantic

from ..models.molecule import Molecule as MoleculeModel


def schedule_svg_gen(mol, user):
    mol['generating_svg'] = True

    session = FuturesSession()

    base_url = Setting().get(PluginSettings.OPENBABEL_BASE_URL)
    if base_url is None:
        base_url = 'http://localhost:5000'

    path = 'convert'
    output_format = 'svg'

    url = '/'.join([base_url, path, output_format])

    data = {
        'format': 'smi',
        'data': mol['smiles']
    }

    hooks = {
        'response': _finish_svg_gen_factory(mol['inchikey'], user)
    }

    future = session.post(url, hooks=hooks, json=data)


def _finish_svg_gen_factory(inchikey, user):
    def _finish_svg_gen(resp, *args, **kwargs):

        query = {
            'inchikey': inchikey
        }

        updates = {}
        updates.setdefault('$unset', {})['generating_svg'] = ''

        if resp.status_code == 200:
            updates.setdefault('$set', {})['svg'] = resp.text
        else:
            print('Generating SVG failed!')
            print('Status code was:', resp.status_code)
            print('Reason was:', resp.reason)

        update_result = super(MoleculeModel,
                              MoleculeModel()).update(query, updates)
        if update_result.matched_count == 0:
            raise ValidationException('Invalid inchikey (%s)' % inchikey)

        return resp

    return _finish_svg_gen


def schedule_3d_coords_gen(mol, user):
    mol['generating_3d_coords'] = True

    # We only need a couple of entries for the job
    inchikey = mol['inchikey']
    smiles = mol['smiles']
    job_mol = {
        'inchikey': inchikey,
        'smiles': smiles
    }
    events.bind('jobs.job.update.after', inchikey,
                callback_factory(inchikey, user))

    job = Job().createLocalJob(
        module='molecules.utilities.async_jobs',
        title='Generate 3d coordinates for SMILES: %s' % smiles,
        user=user, type='molecules.generate_3d_coords', public=False,
        function='_run_3d_coords_gen',
        kwargs={
            'mol': job_mol
        },
        asynchronous=True)
    Job().scheduleJob(job)
    return job


def _run_3d_coords_gen(job):
    jobModel = Job()
    jobModel.updateJob(job, status=JobStatus.RUNNING)

    try:
        mol = job['kwargs']['mol']
        smiles = mol['smiles']
        sdf_data = openbabel.from_smiles(smiles, 'sdf')[0]
        cjson = json.loads(avogadro.convert_str(sdf_data, 'sdf',
                                                'cjson'))
        job['kwargs']['cjson'] = whitelist_cjson(cjson)
        log = 'Finished generating 3d coordinates for %s.' % smiles
        jobModel.updateJob(job, status=JobStatus.SUCCESS, log=log)
    except Exception:
        t, val, tb = sys.exc_info()
        log = '%s: %s\n%s' % (t.__name__, repr(val), traceback.extract_tb(tb))
        jobModel.updateJob(job, status=JobStatus.ERROR, log=log)
        raise


def callback_factory(inchikey, user):

    def callback(event):
        job = event.info['job']

        kwargs = job['kwargs']
        if 'mol' not in kwargs or kwargs['mol'].get('inchikey') != inchikey:
            return

        SUCCESS = JobStatus.SUCCESS
        ERROR = JobStatus.ERROR
        CANCELED = JobStatus.CANCELED

        if job['status'] == SUCCESS:
            query = {
                'inchikey': inchikey
            }
            updates = {}
            updates.setdefault('$set', {})['cjson'] = kwargs.get('cjson')
            updates.setdefault('$unset', {})['generating_3d_coords'] = ''

            update_result = super(MoleculeModel,
                                  MoleculeModel()).update(query, updates)
            if update_result.matched_count == 0:
                raise ValidationException('Invalid inchikey (%s)' % inchikey)

            # Upload the molecule to virtuoso
            try:
                semantic.upload_molecule(MoleculeModel().findOne(query))
            except requests.ConnectionError:
                print(TerminalColor.warning('WARNING: Couldn\'t '
                                            'connect to Jena.'))

        if job['status'] in [SUCCESS, ERROR, CANCELED]:
            events.unbind('jobs.job.update.after', inchikey)

        return

    return callback
