import crypt
import os
import random
import subprocess
import sys
import time

import boto.ec2

IMAGE_ID = 'ami-70f96e40'
KEY_NAME = 'anze'
INSTANCE_TYPE = 't1.micro'
SECURITY_GROUPS = ['quicklaunch-1']
N_INSTANCES = int(sys.argv[1]) if len(sys.argv) > 1 else 1

KEY_FILE = '%s.pem' % KEY_NAME
assert os.path.exists(KEY_FILE), "Key %s does not exist." % KEY_FILE
assert os.stat(KEY_FILE)[0] & 63 == 0, "Key %s should not be world readable." % KEY_FILE

conn = boto.ec2.connect_to_region("us-west-2")

def get_instances(state=None):
    all_instances = []
    for reservation in conn.get_all_instances():
        all_instances.extend(reservation.instances)
    if state:
        return [inst for inst in all_instances if inst.state == state]
    else:
      return all_instances

running_instances = get_instances('running')
#if running_instances:
#  raise Exception("Running instances detected, terminating.")

print "Creating instances"
reservation = conn.run_instances(
  IMAGE_ID,
  key_name=KEY_NAME,
  instance_type=INSTANCE_TYPE,
  security_groups=SECURITY_GROUPS,
  min_count=N_INSTANCES,
  max_count=N_INSTANCES)

print reservation.instances, 'created'

saltchars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
def salt(): return random.choice(saltchars) + random.choice(saltchars)
def hash(plain): return crypt.crypt(plain, salt())

create_users = open('create_users.sh', 'w')
credentials = open('credentials.txt', 'w')
configured_instances = set()
while len(configured_instances) != len(reservation.instances):
  for r in conn.get_all_instances():
    if r.id == reservation.id:
      reservation = r

  pending_instances = []
  for instance in reservation.instances:
    if instance.id in configured_instances:
      continue
    if instance.state != 'running':
      pending_instances.append(instance)
      continue
  
    username = 'student'
    password = ''.join(salt() for x in range(10))
    password_hash = hash(password)
    create_users.write('echo "Configuring %s (%s)"\n' % (instance, instance.ip_address))
    create_users.write('echo "Creating user"\n')
    create_users.write(' '.join(
      ['ssh', '-o', 'UserKnownHostsFile=/dev/null', '-o', 'StrictHostKeyChecking=no',
       '-i', KEY_FILE, 'ubuntu@%s' % instance.ip_address,
       'sudo', 'useradd', '-m', '-p', password_hash, '-G', 'sudo', username]))
    create_users.write('\n')
    create_users.write('echo "Enabling password authentication"\n')
    create_users.write(' '.join(
      ['ssh',  '-o', 'UserKnownHostsFile=/dev/null', '-o', 'StrictHostKeyChecking=no',
       '-i', KEY_FILE, 'ubuntu@%s' % instance.ip_address,
       "\"sudo sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config\""]))
    create_users.write('\n')
    create_users.write(' '.join(
      ['ssh',  '-o', 'UserKnownHostsFile=/dev/null', '-o', 'StrictHostKeyChecking=no',
       '-i', KEY_FILE, 'ubuntu@%s' % instance.ip_address,
       'sudo service ssh reload']))
    create_users.write('\n\n')
    configured_instances.add(instance.id)

    credentials.write("IP: %s\n" % instance.ip_address)
    credentials.write("username: %s\n" % username)
    credentials.write("password: %s\n" % password)
    credentials.write("ssh %s@%s" % (username, instance.ip_address))
    credentials.write("\n")
    
  if not pending_instances:
    break
  sys.stderr.write("Waiting for %s\n" % pending_instances)
  time.sleep(5)

create_users.close()
os.chmod('create_users.sh', 448)
credentials.close()

print 'All instances are running.'

print 'Waiting a minute to make sure ssh services start.'
time.sleep(20)
print 'Create users by executing ./create_users.sh'
