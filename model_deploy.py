import Algorithmia
from datetime import datetime
from git import Repo
from os import environ
from shutil import copyfile
from six.moves.urllib.parse import quote_plus
from tempfile import mkdtemp
from time import sleep

# CONFIGURABLE SETTINGS:

# using a rotating algo name for demo, but this can be any name you prefer; it will be created under https://{ALGORITHMIA_ENDPOINT}/algorithms/[YOUR_USERNAME]
ALGO_NAME = 'digit_recognition_'+datetime.now().strftime('%Y%m%d%H%M%S')

# pick any collection name you prefer; it will be created for you in https://{ALGORITHMIA_ENDPOINT}/data/hosted/
COLLECTION_NAME = 'digit_recognition'

# config your Algorithm details/settings as per https://docs.algorithmia.com/#create-an-algorithm
ALGORITHM_DETAILS = {
    'label': 'Digit Recognition',
    'tagline': 'Digit recognition from an image file'
}
ALGORITHM_SETTINGS = {
    'language': 'python3-1',
    'source_visibility': 'closed',
    'license': 'apl',
    'network_access': 'full',
    'pipeline_enabled': True,
    'environment': 'cpu'
}

# config your publish settings as per https://docs.algorithmia.com/#publish-an-algorithm
ALGORITHM_VERSION_INFO = {
    'sample_input': 'https://github.com/algorithmiaio/sample-apps/blob/master/algo-dev-demo/digit_recognition/images/digit_1.png?raw=true'
}

# path within this repo where the algo.py, requirements.txt, and model file are located
ALGO_TEMPLATE_PATH = 'algorithm_template/'

# name of the model file to be uploaded to Hosted Data
MODEL_FILE = 'digits_classifier.pkl'

# if you need to update the contents of algo.py during deployment, do so here


def UPDATE_ALGORITHM_TEMPLATE(file_contents):
    return file_contents.replace('data://username/demo/'+MODEL_FILE, data_path+'/'+MODEL_FILE)


# DEPLOYMENT SCRIPT:

# verify that environment keys are set
api_key = environ.get('ALGORITHMIA_API_KEY')
algo_domain = environ.get('ALGORITHMIA_DOMAIN')
algo_endpoint = f"https://{algo_domain}"
username = environ.get('ALGORITHMIA_USERNAME')
if not api_key:
    raise SystemExit(
        'Please set the environment variable ALGORITHMIA_MANAGEMENT_API_KEY (key must have permission to manage algorithms)')
if not algo_domain:
    raise SystemExit(
        'Please set the environment variable ALGORITHMIA_DOMAIN (e.g. algorithmia.com')
if not username:
    raise SystemExit(
        'Please set the environment variable ALGORITHMIA_USERNAME')

# set up Algorithmia client and path names
algo_full_name = username+'/'+ALGO_NAME
data_path = 'data://'+username+'/'+COLLECTION_NAME
client = Algorithmia.client(api_key, algo_endpoint)
algo = client.algo(algo_full_name)
algo.set_options(timeout=300)  # optional

# create Hosted Data collection
print('CREATING '+data_path)
print(f"ON Algorithmia cluster: {algo_endpoint}")
if not client.dir(data_path).exists():
    client.dir(data_path).create()

# upload the model file
print('UPLOADING model to '+data_path+'/'+MODEL_FILE)
client.file(data_path+'/'+MODEL_FILE).putFile(ALGO_TEMPLATE_PATH+MODEL_FILE)

# create the Algorithm
print(f"CREATING algorithm: {algo_full_name}")
print(f"ON Algorithmia cluster: {algo_endpoint}")
try:
    print(algo.create(details=ALGORITHM_DETAILS, settings=ALGORITHM_SETTINGS))
except Exception as x:
    raise SystemExit(
        'ERROR: cannot create {}: if the Algorithm already exists and you wish to overwrite it, remove/ignore this step\n{}'.format(algo_full_name, x))

# git clone the created algorithm's repo into a temp directory
tmpdir = mkdtemp()
encoded_api_key = quote_plus(api_key)
algo_repo = f"https://{username}:{encoded_api_key}@git.{algo_domain}/git/{algo_full_name}.git"
print(f"CLONING serving repo: {algo_repo}")
print(f"To local: {tmpdir}")
cloned_repo = Repo.clone_from(algo_repo, tmpdir)

# Add algo.py into repo
print('ADDING algorithm files...')
algorithm_file_name = '{}.py'.format(algo_full_name.split('/')[1])
# Add requirements.txt into repo
copyfile(ALGO_TEMPLATE_PATH+'requirements.txt', tmpdir+'/requirements.txt')
print(f"Copied requirements.txt to {tmpdir}/requirements.txt")
# Add README.md into repo
copyfile(ALGO_TEMPLATE_PATH+'README.md', tmpdir+'/README.md')
print(f"Copied README.md to {tmpdir}/README.md")

# Update the algorithm (replacing template values)
algo_template = f"{ALGO_TEMPLATE_PATH}algo.py"
algo_to_push = f"{tmpdir}/src/{algorithm_file_name}"
with open(algo_template, 'r+') as file_in:
    with open(algo_to_push, 'w+') as file_out:
        file_out.write(UPDATE_ALGORITHM_TEMPLATE(file_in.read()))
print(f"Wrote algorithm file '{algo_to_push}' from template '{algo_template}'")

cloned_repo.git.add(all=True)
cloned_repo.index.commit('Add algorithm files')

# push changes (implicitly causes Algorithm to recompile on server)
print('PUSHING local files to serving repo')
origin = cloned_repo.remote(name='origin')
origin.push()

# wait for compile to complete, then publish the Algorithm
print('PUBLISHING '+algo_full_name)
sleep(15)
try:
    results = algo.publish(version_info=ALGORITHM_VERSION_INFO)
except:
    # print('RETRYING: if this occurs repeatedly, increase the sleep() time before the PUBLISH step to allow for compilation time')
    try:
        sleep(60)
        results = algo.publish(
            settings={
                "algorithm_callability": "private"
            },
            version_info={
                "release_notes": "Automatically created, deployed and published from Jenkins.",
                "sample_input": "https://commons.wikimedia.org/wiki/File:Digital_Digits.png",
                "version_type": "minor",
            },
            details=ALGORITHM_DETAILS
        )
    except Exception as x:
        raise SystemExit(
            'ERROR: unable to publish Algorithm: code will not compile, or compile takes too long\n{}'.format(x))
print(results)
print(
    f"DEPLOYED version {results.version_info.semantic_version} to {algo_endpoint}/algorithms/{algo_full_name}")
