#!groovy

pipeline {

  // agent defines where the pipeline will run.
  agent {
    label "windows"
  }
  
  triggers {
    cron('H */3 * * *')
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
    
  }
  
  post {
    always {
        junit "test-reports/**/*.xml"
    }
  }
  
  // The options directive is for configuration that applies to the whole job.
  options {
    buildDiscarder(logRotator(numToKeepStr:'20', daysToKeepStr: '28'))
    timeout(time: 60, unit: 'MINUTES')
  }
}
