Install requirements using

  pip install -r requirements.txt

Create boto configuration files containing your credentials:

  $ cat ~/.boto
  [Credentials]
  aws_access_key_id = <your access key>
  aws_secret_access_key = <your secret key>

Modify the first few lines int create_instances.py to match your deisred settings.
Copy your private key to the directory containing the script.

To create ec2 instances run:

  python create_instances.py

Followed by:

  ./create_users.sh  
