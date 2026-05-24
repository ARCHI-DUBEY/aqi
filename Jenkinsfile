pipeline {
    agent any

    stages {

        stage('Clone') {
            steps {
                git branch: 'main',
                url: 'https://github.com/ARCHI-DUBEY/aqi.git'
            }
        }

        stage('Build Docker Image') {
            steps {
                bat 'docker build -t aqi-pulse .'
            }
        }

        stage('Verify Image') {
            steps {
                bat 'docker images'
            }
        }

    }

    post {
        success {
            echo 'Docker build successful'
        }

        failure {
            echo 'Pipeline failed'
        }
    }
}