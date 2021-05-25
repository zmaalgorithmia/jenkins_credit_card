pipeline {
    agent any
    options {
        skipStagesAfterUnstable()
    }
    environment {
        ALGORITHMIA_DOMAIN = 'algosales.productionize.ai'
        GIT_CONFIG_NOSYSTEM = '1'
        PYTHONUNBUFFERED = '1'
    }
    stages {
        // stage('Build') {
        //     steps {
        //         checkout([$class: 'GitSCM', branches: [[name: '*/main']],
        //         userRemoteConfigs: [[url: 'https://github.com/ddreakfordalgorithmia/jenkins_deploy_to_algorithmia.git']]])
        //     }
        // }
        stage('Deploy') {
            steps {
                // use a python environment with: algorithmia>=1.2.0, gitpython>=2.1.0, six>=1.12.0
                withPythonEnv('Python-3.8') {
                    sh 'pip install -r jenkins_deploy_algorithmia/requirements.txt'
                    sh 'python jenkins_deploy_algorithmia/model_deploy.py'
                }
            }
        }
    }
}
