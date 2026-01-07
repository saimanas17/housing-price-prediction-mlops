pipeline {
    agent any
    
    environment {
        // Docker Hub configuration
        DOCKER_REGISTRY = 'saimanasg'
        DOCKER_CREDENTIALS_ID = 'dockerhub-credentials'
        
        // Image names
        BENTO_IMAGE = "${DOCKER_REGISTRY}/housing-bento"
        FRONTEND_IMAGE = "${DOCKER_REGISTRY}/housing-frontend"
        
        // Git configuration
        GIT_CREDENTIALS_ID = 'github-credentials'
        GIT_USER_EMAIL = 'gourabathini.s@northeastern.edu'
        GIT_REPO = 'housing-price-prediction-mlops'
        
        
    }
    
    stages {
	stage('Checkout') {
            steps {
                echo '📥 Checking out source code...'
                checkout scm
            }
        }        
        
        stage('Service Selection') {
            steps {
                script {
                    try {
                        timeout(time: 30, unit: 'SECONDS') {
                            env.SELECTED_SERVICE = input(
                                message: 'Which service to build? (Defaults to "all" in 30s)',
                                parameters: [
                                    choice(
                                        name: 'SERVICE',
                                        choices: ['all', 'bento', 'frontend'],
                                        description: 'Select service'
                                    )
                                ]
                            )
                        }
                    } catch (err) {
                        echo '⏱️  Timeout - defaulting to "all"'
                        env.SELECTED_SERVICE = 'all'
                    }
                    echo "✅ Building: ${env.SELECTED_SERVICE}"
                }
            }
        }
        
        stage('Determine Version') {
            steps {
                script {
                    env.VERSION_TAG = "v${BUILD_NUMBER}"
                    echo "🏷️  Version tag: ${VERSION_TAG}"
                }
            }
        }
        
    stage('Build BentoML Service') {
    when {
        expression { env.SELECTED_SERVICE == 'all' || env.SELECTED_SERVICE == 'bento' }
    }
    steps {
        script {
            echo "🔨 Building BentoML Docker image..."
            
            dir('bentoml') {
                sh """
                    # Use manas user's bentoml
                    sudo -u manas /home/manas/.local/bin/bentoml build
                    
                    # Get the latest Bento tag
                    BENTO_TAG=\$(sudo -u manas /home/manas/.local/bin/bentoml list | grep housing-predictor | head -1 | awk '{print \$1}')
                    echo "Built Bento: \$BENTO_TAG"
                    
                    sudo -u manas /home/manas/.local/bin/bentoml containerize \$BENTO_TAG -t ${BENTO_IMAGE}:${VERSION_TAG}
					docker tag ${BENTO_IMAGE}:${VERSION_TAG} ${BENTO_IMAGE}:latest
                    
                """
            }
        }
    }
}
        
        stage('Build Frontend') {
            when {
                expression { env.SELECTED_SERVICE == 'all' || env.SELECTED_SERVICE == 'frontend' }
            }
            steps {
                script {
                    echo "🔨 Building Frontend Docker image..."
                    
                    dir('frontend') {
                        sh """
                            docker build -t ${FRONTEND_IMAGE}:${VERSION_TAG} .
                            docker tag ${FRONTEND_IMAGE}:${VERSION_TAG} ${FRONTEND_IMAGE}:latest
                            
                            echo "✅ Built: ${FRONTEND_IMAGE}:${VERSION_TAG}"
                        """
                    }
                }
            }
        }
        
        stage('Push to Docker Hub') {
            steps {
                script {
                    echo '📤 Pushing images to Docker Hub...'
                    
                    withCredentials([usernamePassword(
                        credentialsId: "${DOCKER_CREDENTIALS_ID}",
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                    )]) {
                        sh 'echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin'
                        
                        if (env.SELECTED_SERVICE == 'all' || env.SELECTED_SERVICE == 'bento') {
                            sh """
                                docker push ${BENTO_IMAGE}:${VERSION_TAG}
                                docker push ${BENTO_IMAGE}:latest
                                echo "✅ Pushed BentoML image"
                            """
                        }
                        
                        if (env.SELECTED_SERVICE == 'all' || env.SELECTED_SERVICE == 'frontend') {
                            sh """
                                docker push ${FRONTEND_IMAGE}:${VERSION_TAG}
                                docker push ${FRONTEND_IMAGE}:latest
                                echo "✅ Pushed Frontend image"
                            """
                        }
                        
                        sh 'docker logout'
                    }
                }
            }
        }
        
        stage('Update Manifests') {
            steps {
                script {
                    echo '📝 Updating Kubernetes manifests...'
                    
                    if (env.SELECTED_SERVICE == 'all' || env.SELECTED_SERVICE == 'bento') {
                        sh """
                            sed -i 's|image: ${BENTO_IMAGE}:.*|image: ${BENTO_IMAGE}:${VERSION_TAG}|g' app-k8s/bento-complete.yaml
                            echo "✅ Updated bento-complete.yaml"
                        """
                    }
                    
                    if (env.SELECTED_SERVICE == 'all' || env.SELECTED_SERVICE == 'frontend') {
                        sh """
                            sed -i 's|image: ${FRONTEND_IMAGE}:.*|image: ${FRONTEND_IMAGE}:${VERSION_TAG}|g' app-k8s/frontend-deployment.yaml
                            echo "✅ Updated frontend-deployment.yaml"
                        """
                    }
                }
            }
        }
        
        stage('Commit to Git') {
            steps {
                script {
                    echo '📤 Pushing changes to Git...'
                    
                    withCredentials([usernamePassword(
                        credentialsId: "${GIT_CREDENTIALS_ID}",
                        usernameVariable: 'GIT_USER',
                        passwordVariable: 'GIT_TOKEN'
                    )]) {
                        sh """
                            git config user.email "${GIT_USER_EMAIL}"
                            git config user.name "\${GIT_USER}"
                            
                            git add app-k8s/
                            
                            if git diff --staged --quiet; then
                                echo "No changes to commit"
                            else
                                git commit -m "Build ${BUILD_NUMBER}: Update ${env.SELECTED_SERVICE} to ${VERSION_TAG} [skip ci]"
                                git push https://\${GIT_USER}:\${GIT_TOKEN}@github.com/saimanas17/${GIT_REPO}.git HEAD:refs/heads/master
                                echo "✅ Pushed to Git"
                            fi
                        """
                    }
                }
            }
        }
    }
    
    post {
        always {
            sh """
                docker rmi ${BENTO_IMAGE}:${VERSION_TAG} || true
                docker rmi ${FRONTEND_IMAGE}:${VERSION_TAG} || true
            """
        }
        success {
            echo "✅ Build ${BUILD_NUMBER} completed successfully!"
        }
        failure {
            echo "❌ Build ${BUILD_NUMBER} failed!"
        }
    }
}
