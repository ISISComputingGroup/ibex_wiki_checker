#!groovy

pipeline {

  // agent defines where the pipeline will run.
  agent {  
    label {
      label "IBEX_wiki_checker"
    }
  }
  
  triggers {
    cron('H 1 * * *')
  }
  
  stages {  
    stage("Checkout") {
      steps {
        checkout scm
      }
    }
    
    stage("Build") {
      steps {
        
        bat """
            call run_tests.bat || echo "running tests failed."
            """
      }
    }
    
    stage("Unit Test Results") {
      steps {
        junit "test-reports/**/*.xml"
      }
   }
  }
  
  post {
    failure {
      step([$class: 'Mailer', notifyEveryUnstableBuild: true, recipients: 'icp-buildserver@lists.isis.rl.ac.uk', sendToIndividuals: true])
    }    
  }
  
  // The options directive is for configuration that applies to the whole job.
  options {
    buildDiscarder(logRotator(numToKeepStr:'20', daysToKeepStr: '28'))
    timeout(time: 60, unit: 'MINUTES')
    disableConcurrentBuilds()
  }
}
