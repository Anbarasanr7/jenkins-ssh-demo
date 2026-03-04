pipeline {
  agent {
    dockerfile {
      filename 'Dockerfile.jenkins'
      // Expose SSH port from job container to Jenkins agent host
      args '-p 2222:2222'
      reuseNode true
    }
  }

  options {
    timestamps()
    disableConcurrentBuilds() // avoids port collision for sample
  }

  parameters {
    booleanParam(name: 'ENABLE_SSH_DEBUG', defaultValue: false, description: 'Enable live SSH debug session')
    choice(name: 'DEBUG_TRIGGER', choices: ['always', 'on_failure'], description: 'Open SSH session always or only on test failure')
    string(name: 'DEBUG_GITHUB_USER', defaultValue: '', description: 'GitHub username whose public keys are allowed')
    string(name: 'DEBUG_HOST', defaultValue: 'REPLACE_WITH_AGENT_IP_OR_DNS', description: 'Host/IP reachable from your laptop')
    string(name: 'DEBUG_TIMEOUT_MIN', defaultValue: '30', description: 'How long to keep SSH session open')
    booleanParam(name: 'FORCE_FAIL', defaultValue: false, description: 'Demo switch: force tests to fail')
  }

  environment {
    TEST_EXIT_CODE = '0'
    DEBUG_PORT = '2222'
  }

  stages {
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Test') {
      steps {
        script {
          def cmd = params.FORCE_FAIL ? 'FORCE_FAIL=true pytest -q' : 'pytest -q'
          def code = sh(script: cmd, returnStatus: true)
          env.TEST_EXIT_CODE = "${code}"
          if (code != 0) {
            currentBuild.result = 'FAILURE' // mark red but continue to debug stage
          }
        }
      }
    }

    stage('SSH Debug Session') {
      when {
        expression {
          params.ENABLE_SSH_DEBUG && (params.DEBUG_TRIGGER == 'always' || env.TEST_EXIT_CODE != '0')
        }
      }
      steps {
        script {
          if (!params.DEBUG_GITHUB_USER?.trim()) {
            error('DEBUG_GITHUB_USER is required when ENABLE_SSH_DEBUG=true')
          }
        }

        sh '''
          set -euxo pipefail
          mkdir -p /root/.ssh
          chmod 700 /root/.ssh

          curl -fsSL "https://github.com/${DEBUG_GITHUB_USER}.keys" > /root/.ssh/authorized_keys
          test -s /root/.ssh/authorized_keys
          chmod 600 /root/.ssh/authorized_keys

          cat >/tmp/sshd_config <<EOF
Port ${DEBUG_PORT}
ListenAddress 0.0.0.0
HostKey /etc/ssh/ssh_host_ed25519_key
HostKey /etc/ssh/ssh_host_rsa_key
PubkeyAuthentication yes
PasswordAuthentication no
KbdInteractiveAuthentication no
ChallengeResponseAuthentication no
PermitRootLogin prohibit-password
UsePAM no
AuthorizedKeysFile /root/.ssh/authorized_keys
PidFile /tmp/sshd.pid
PrintMotd no
EOF

          /usr/sbin/sshd -f /tmp/sshd_config -E /tmp/sshd.log

          echo "====================================================="
          echo "SSH debug is ACTIVE"
          echo "Run from your laptop:"
          echo "ssh -p ${DEBUG_PORT} root@${DEBUG_HOST}"
          echo "After login, go to workspace:"
          echo "cd ${WORKSPACE}"
          echo "====================================================="
        '''

        timeout(time: params.DEBUG_TIMEOUT_MIN as Integer, unit: 'MINUTES') {
          input message: 'SSH debug active. Click Proceed to end session.', ok: 'Proceed'
        }
      }
      post {
        always {
          sh '''
            set +e
            if [ -f /tmp/sshd.pid ]; then
              kill "$(cat /tmp/sshd.pid)"
            fi
          '''
        }
      }
    }

    stage('Fail Build If Tests Failed') {
      when {
        expression { env.TEST_EXIT_CODE != '0' }
      }
      steps {
        error('Tests failed (debug stage has already executed if enabled).')
      }
    }
  }
}
