Install requirements using

  pip install -r requirements.txt

Create boto configuration files containing your credentials:

  $ cat ~/.boto
  [Credentials]
  aws_access_key_id = <your access key>
  aws_secret_access_key = <your secret key>

In order to run the script, you need to configure your credentials and instance options in create_instances script and enter names of students to the students.txt file (one per line).

To create ec2 instances run:

  python create_instances.py

Followed by:

  ./create_users.sh  

The script will tag names of the students to the names of the virtual machines for easier administration.
