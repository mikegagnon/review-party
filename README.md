# Clubby-1

heroku config:set WEB_CONCURRENCY=1

local: brew install poppler
heroku: Aptfile + https://elements.heroku.com/buildpacks/heroku/heroku-buildpack-apt

Except where otherwise noted, everything in this repository is copyrighted by
Michael N. Gagnon, 2020.

# What is Clubby-1?

Clubby is a minimal heroku compatible web framework, built on top of flask. Clubby-1
is version 1 (not semantic versioning).

Pretty much the only features implemented are account management features.

## How to use

Copy the codebase into a brand new directory. Delete .git, then git init, then follow this guide.

Also, delete the venv directory, and requirements.txt, if you feel like it

### .html

Search for clubby in all html files, and replace Clubby with your project name

### clubby.sql

Rename to projectname.sql or something

### package.json

Or maybe just delete this file and re-init node

Replace "clubby-1" with "projectname"

Update github urls

### package-lock.json

Or maybe just delete this file and re-init node


Same thing, replace "clubby-1" with "projectname"

### clubby-export.sh

Create a "secret" file ~/projectname-export.sh, or copy and modify it from ~/clubby-export.sh

    export SECRET_KEY="secret goes here"
    export DATABASE_URL="postgres://clubbyuser:password@localhost:5444/clubbydb"
    export FLASK_EMAIL_PASSWORD="password goes here"
    export FLASK_EMAIL_SERVER="server goes here "
    export ADMIN_EMAIL="email address goes here"
    export NOREPLY_EMAIL="email address goes here"
    export STYLED_DOMAIN_NAME="ClubbyFoo.com"

#  Development-environment setup instructions

## First, setup Virtual Box (for the postgresql server), if you haven't already

<BEGIN UBUNTU INSTALLATION AND SETUP>

Download the MacOS version of Virtual Box (I'm using version Version 6.1.16 r140961 (Qt5.6.3)
), since I assume you're running MacOS: https://www.virtualbox.org/wiki/Downloads

You probably need to change the Security and Privacy settings, during the install process, to unblock "Oracle America, Inc." Just find the allow button, then click it. Then, re-run the install software.

I've got a 6-core, 16-GB-memory machine, so my settings for my VM might not be good for you.

Download Ubuntu Desktop, ISO file. I'm using Ubuntu 20.04.1 LTS, ubuntu-20.04.1-desktop-amd64.iso. 

Install Ubuntu into Virtual Box. Settings I chose:

- Name: postserver
- 4000 MB of memory
- Create a virtual hard disk now
- VDI (VirtualBox Disk Image)
- *Fixed Size* for storage on physical hard disk
- 20 GB of disk storage

Now, to install Ubuntu

- Update system settings to allow VB to intercept keystrokes from everywhere (you'll probably need to restart VB)
- Oh no, but now the VB start button doesn't work. Investigating
- Right clicked IDE Secondary Master, and popped in Ubuntu. Still can't start VM.
- Found this: "Possibly there's an orphaned VBoxSVC process still running. You could try stopping it with Task Manager, or simply reboot the host. Shut down all VMs of course before doing any of that."
- Rebooting, killed VB, resurrection good
- Booting up Ubunutu install disk
- "Normal installation"
- "Download updates when installing Ubuntu"
- "Erase disk and install Ubuntu"
- "Install now"
- Username: match your MacOS username
- ...
- Once you've installed the OS, it will probably prompt you to install updates. Go for it if you feel like it, then restart OS. I did.
- Oh no, Ubuntu corrupted now. Reinstalling VM...
- This time going for minimal installation, and ignoring prompt after install to install updates.


Now, install VirtualBox additions to the VM
- But first, take a snapshot (1)
- Then https://askubuntu.com/questions/1035030/virtualbox-guest-additions-installation-problem
- Then reboot
- Then install additions
- Then reboot
- Then snapshot (2)


https://www.virtual-dba.com/installing-postgresql-ubuntu-virtualbox/

$ wget -q https://www.postgresql.org/media/keys/ACCC4CF8.asc -O- | sudo apt-key add -
$ echo "deb http://apt.postgresql.org/pub/repos/apt/ bionic-pgdg main" | sudo tee /etc/apt/sources.list.d/postgresql.list
$ sudo apt update


https://www.postgresql.org/download/linux/ubuntu/

    # Create the file repository configuration:
    sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'

    # Import the repository signing key:
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

    # Update the package lists:
    sudo apt-get update

    # Install the latest version of PostgreSQL.
    # If you want a specific version, use 'postgresql-12' or similar instead of 'postgresql':
    sudo apt-get -y install postgresql

$ sudo -u postgres -i
$ psql

postgres# 


Oops, forgot about SSH

$ sudo apt-get install openssh-server

fail

$ sudo apt-get update
$ sudo apt-get upgrade

again: $ sudo apt-get install openssh-server

fail

Let's try aptitude
$ sudo apt-get install aptitude
$ sudo aptitude install openssh-server

Select Yes: accept proposed solution

Ok, that didn;t do anything

https://askubuntu.com/questions/546983/ssh-installation-errors
$ sudo aptitude install openssh-client=1:8.2p1-4
$ sudo apt-get install openssh-server




$ sudo service ssh status

good!

now setup ssh keys, and port forwarding 2222 to 22

https://nsrc.org/workshops/2014/btnog/raw-attachment/wiki/Track2Agenda/ex-virtualbox-portforward-ssh.htm

    $ scp -P 2222 ~/.ssh/id_rsa.pub localhost:
    $ ssh localhost -p 2222
    $$ cat id_rsa.pub >> ~/.ssh/authorized_keys 


Now, let's setup a db over ssh

$ sudo -u postgres -i
$ psql

postgres=# create database postdb;
postgres=# create user gomden with encrypted password 'gomden';
postgres=# grant all privileges on database postdb to gomden;


Now, let's a poke a hole in the guest firewall:
https://blog.logrocket.com/setting-up-a-remote-postgres-database-server-on-ubuntu-18-04/

Which ends with

$ sudo ufw allow 5432/tcp
$ sudo systemctl restart postgresql

<END UBUNTU INSTALLATION AND SETUP>



## MacOS Setup

### npm

https://nodejs.org/en/

### virtualenv 

https://gist.github.com/pandafulmanda/730a9355e088a9970b18275cb9eadef3

$ pip3 install virtualenv

## Here is how I began my setup by doing some python things

    virtualenv venv
    . venv/bin/activate
    pip3.8 install flask
    pip3.8 install flask_wtf
    pip3.8 install psycopg2 # see note below
    pip3.8 install itsdangerous
    pip3.8 install celery
    pip3.8 install flask_sslify
    pip3.8 install flask_mail
    pip3.8 install flask_bcrypt 
    pip3.8 install redis
    pip3.8 install gunicorn
    pip3.8 install eventlet
    pip3.8 freeze > requirements.txt

###  Error: pg_config executable not found.

https://postgresapp.com/
update the path in ~/.bash_profile : https://stackoverflow.com/questions/20170895/mac-virtualenv-pip-postgresql-error-pg-config-executable-not-found/26694779

export PATH="$PATH:/Applications/Postgres.app/Contents/Versions/13/bin"
source ~/.bash_profile

$ pg_config --version

## Here is how I setup redis

https://redis.io/download

    make
    make install

## Later, when launching the app, you will need to run redis in a terminal

    redis-server

## Here is how I setup the database locally

Replace clubbydb with the name of your database.

Replace clubbyuser with something else.

Using a password of 'password' is probably fine, since it's just your private dev environment.

    ssh localhost -p 2222
    sudo -u postgres psql
    postgres=# CREATE DATABASE rpdb;
    postgres=# CREATE user rpuser with encrypted password 'password';
    postgres=# GRANT all privileges on database rpdb to rpuser;

## Here is how I initialized the tables

Use projectname.sql instead of clubby.sql, etc.

    scp -P 2222 rp.sql localhost:
    ssh localhost -p 2222
    psql rpuser -h 127.0.0.1 -d rpdb -a -f rp.sql

## If you want to log into the db as rpuser

    ssh localhost -p 2222
    psql rpuser -h 127.0.0.1 -d rpdb -a
    rpdb=>

And, just in case, this might come in handy:

    postgres=# \connect rpdb


## Here is how I setup Babel

I followed some of these steps: https://ccoenraets.github.io/es6-tutorial/setup-babel/

    npm init
    npm install babel-cli babel-core --save-dev
    npm install babel-preset-es2015 --save-dev
    npm install npm-watch

### Then, I did some copy and paste on package.json

    "scripts": {
        "build": "babel --presets es2015 source/js/ -d core_gomden/static/js/my/",
        "watch": "npm-watch"
    },

and

    "watch": {
        "build": "source/js/*.js"
    }

## Rename and edit rp-export.sh in home directory

    export SECRET_KEY="..."
    export DATABASE_URL="postgres://rpuser:password@localhost:5444/rpdb"
    export FLASK_EMAIL_PASSWORD="..."
    export FLASK_EMAIL_SERVER="..."
    export ADMIN_EMAIL="..."
    export NOREPLY_EMAIL="..."
    export STYLED_DOMAIN_NAME="..."


## Every time you want to launch the system

Launch pipeline-server in Virtual Box
    
In one tab:

    . venv/bin/activate
    source export.sh
    source ~/rp-export.sh
    python3.8 -m flask run

Another tab:

    redis-server

Another tab:

    . venv/bin/activate
    source export.sh
    source ~/rp-export.sh
    celery -A gomden.celery worker -l info

Another tab:
    
    npm run watch

Or,
    
    npm run build
