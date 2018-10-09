def gh_branch = 'master'
def gh_repo = 'github.com/status-im/analytics.status.im.git'
def gh_user = 'status-im-auto'
def gh_email = 'auto@status.im'

node('linux') {
  stage('Git Prep') {
    checkout scm
    dir('analytics') {
      git(url: "https://${gh_repo}")
    }
    sh "git config user.name ${gh_user}"
    sh "git config user.email ${gh_email}"
    sh "git config --global push.default simple"
    /* Install Python3 requirements */
    sh 'pip3 install --user -r requirements.txt'
  }

  stage('Gen AppFigures Stats') {
    withCredentials([
      string(credentialsId: 'appfigures-key',       variable: 'CLIENT_KEY'),
      string(credentialsId: 'appfigures-header',    variable: 'AUTH_HEADER'),
    ]) {
      sh './appfigures.py analytics'
    }
  }

  stage('Gen Whisper Stats') {
    sh './prometheus.py analytics'
  }

  stage('Push Changes') {
    withCredentials([
      string(credentialsId: 'jenkins-github-token', variable: 'GH_TOKEN'),
    ]) {
      def gh_url = "https://${gh_user}:${env.GH_TOKEN}@${gh_repo}"
      dir('analytics') {
        sh 'git commit -m "update analytics-dash images" .'
        sh "git push ${gh_url} ${gh_branch}"
      }
    }
  }
}
