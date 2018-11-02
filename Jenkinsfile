#!/usr/bin/env groovy

@Library('lco-shared-libs@0.0.12') _

pipeline {
    agent any
    environment {
        dockerImage = null
        GIT_DESCRIPTION = gitDescribe()
        GIT_AUTHOR = sh(
            script: 'git log -1 --pretty=format:%an',
            returnStdout: true
        )
        GIT_AUTHORED_DATE = sh(
            script: 'git log -1 --pretty=format:%ai',
            returnStdout: true
        )
        PROJ_NAME = projName()
        //
        TAG = sh(returnStdout: true, script: "git tag --contains | head -1").trim()
        DOCKER_IMG = dockerImageName("${LCO_DOCK_REG}", "${PROJ_NAME}", "${GIT_DESCRIPTION}")
    }
    stages {
        stage('Set Environment') {
            when{ buildingTag() }
            steps {
                script {
                    DOCKER_IMG = dockerImageName("${LCO_DOCK_REG}", "${PROJ_NAME}", "${TAG}")
                }
            }
        }
        stage('Build Docker Image') {
            steps {
                script {
                    dockerImage = docker.build("$DOCKER_IMG")
                }
            }
        }
        stage('Run Tests') {
            environment {
                LAKE_URL = 'http://lakedevfake.lco.gtn'
                CONFIGDB_URL = 'http://configdbdevfake.lco.gtn'
                VALHALLA_URL = 'http://valhalladevfake.lco.gtn'
            }
            steps {
                sh 'docker run --rm "${DOCKER_IMG}" /bin/bash -c "./manage.py test --settings=test_settings"'
            }
        }
        stage('Deploy') {
            when {
                allOf {
                    branch 'master';
                    buildingTag()
                }
            }
            // push the current tagged docker image
            environment {
                AWS_ACCESS_KEY_ID = credentials('valhalla-aws-access-key')
                AWS_SECRET_ACCESS_KEY = credentials('valhalla-aws-secret-key')
                MEDIA_STORAGE = 'split_storage.MediaStorage'
                STATIC_STORAGE = 'split_storage.StaticStorage'
            }
            steps {
                script {
                    dockerImage.push()
                }
                sh 'docker run --rm -e AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} -e AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} -e MEDIA_STORAGE=${MEDIA_STORAGE} -e STATIC_STORAGE=${STATIC_STORAGE} "${DOCKER_IMG}" /bin/bash -c "./manage.py collectstatic --noinput"'
            }
        }
    }
}