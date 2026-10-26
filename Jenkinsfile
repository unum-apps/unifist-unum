pipeline {
    agent any

    environment {
        VERSION = GIT_COMMIT.take(7)
    }

    stages {
        stage('build') {
            parallel {
                stage('api') {
                    stages {
                        stage('image') {
                            steps {
                                dir('api') {
                                    sh 'make image -e VERSION=${VERSION}'
                                }
                            }
                        }
                        stage('ddl') {
                            steps {
                                dir('api') {
                                    sh 'make ddl -e VERSION=${VERSION}'
                                }
                            }
                        }
                        stage('test') {
                            steps {
                                dir('api') {
                                    sh 'make test -e VERSION=${VERSION} NETWORK=$([ -n "$CHANGE_ID" ] && echo "pr-$CHANGE_ID" || echo ${VERSION})-unifist-unum.io'
                                }
                            }
                        }
                        stage('lint') {
                            steps {
                                dir('api') {
                                    sh 'make lint -e VERSION=${VERSION}'
                                }
                            }
                        }
                    }
                }
                stage('gui') {
                    stages {
                        stage('image') {
                            steps {
                                dir('gui') {
                                    sh 'make image -e VERSION=${VERSION}'
                                }
                            }
                        }
                    }
                }
            }
        }
        stage('setup') {
            steps {
                sh 'make setup'
            }
        }
        stage('push') {
            when {
                branch 'main'
            }
            stages {
                stage('hash') {
                    parallel {
                        stage('api') {
                            steps {
                                dir('api') {
                                    sh 'make push -e VERSION=${VERSION}'
                                }
                            }
                        }
                        stage('gui') {
                            steps {
                                dir('gui') {
                                    sh 'make push -e VERSION=${VERSION}'
                                }
                            }
                        }
                    }
                }
                stage('semver') {
                    steps {
                        sh 'make semver -e VERSION=${VERSION}'
                    }
                }
            }
        }
        stage('tag') {
            // Only main, so other apps can install this version from its tag. make tag does nothing if the tag is already there
            when {
                branch 'main'
            }
            // A tag needs a committer, and Jenkins has none
            environment {
                GIT_COMMITTER_NAME = 'Leroy Jenkins'
                GIT_COMMITTER_EMAIL = 'leroy@jenkins.klot.io'
            }
            steps {
                withCredentials([usernamePassword(credentialsId: 'github', usernameVariable: 'GH_USER', passwordVariable: 'GH_TOKEN')]) {
                    // Jenkins checks out a detached commit and VERSION here is the commit, so the tag is the version file's
                    sh '''
                        git checkout -B main
                        git remote set-url origin "https://$GH_USER:$GH_TOKEN@${GIT_URL#https://}"
                        make tag VERSION=$(cat VERSION)
                    '''
                }
            }
        }
    }
}
