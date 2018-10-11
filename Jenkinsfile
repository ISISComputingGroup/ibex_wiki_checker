#!groovy

pipeline {

  // agent defines where the pipeline will run.
  agent {
    label "!linux"
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
            call run_tests.bat
            """
      }
    }
    
    stage("Unit Test Results") {
      steps {
        junit "test-reports/**/*.xml"
      }
   }
  }
  
  // The options directive is for configuration that applies to the whole job.
  options {
    buildDiscarder(logRotator(numToKeepStr:'20', daysToKeepStr: '28'))
    timeout(time: 60, unit: 'MINUTES')
    disableConcurrentBuilds()
  }
}
