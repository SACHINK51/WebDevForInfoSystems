# WebDevForInfoSystems
A Full stack online book store web application

Steps to setup and deploy the system:

The Flask-based Book Store web application setup, deployment involves the following tasks:

Server Environment Setup:

Go to https://azure.microsoft.com
Create an account
Click Home
Click Virtual machines
Click Create
Click Azure virtual machine

Type the following details under the following sections:
Instance Details:

Virtual machine name: Type the virtual machine name
Region: Select the closest region
Images: Select the Ubuntu Server image : Ubuntu Server 20.04 LTS - x64 Gen2
VM architecture: x64

Administrator account:
Authentication type: SSH public key
Username: <your username>
SSH public key source: Use existing public key

Go to your Virtual Machine command line interface and run:
ssh-keygen
cat .\ssh\id_rsa.pub
Copy the public key and paste it into the SSH public key source box.

Public inbound port rules:
Public inbound ports: Allow selected ports
Select inbounds ports: select the following ports
22 for SSH
80 for HTTP
443 for HTTPS
Click Create to complete the Virtual machine creation

Configure Domain:
Set up DNS records to point your domain/subdomain to the public IP address of your Azure Virtual Machine.
Click home
Click Virtual Machines
Click the Created Virtual machine
Next to DNS name, click Not configured
In the DNS name label type the name label(Make it short with all small letters)
Click Save
Click Refresh
Copy the displayed DNS Name

Configure Your Virtual Machine:
Connect to the Virtual machine using ssh from the Administrator’s client machine:
Add the server public key to the client machine’s ~/.ssh/authorized_keys file
Make the authorized_keys file readable by the user who will be using SSH to connect to the server.
chmod 600 ~/.ssh/authorized_keys

Connect to the following command from the administrator machine’s command line:
ssh <virtual machine user name>@<domain name>

Install Required Packages: Install necessary software and dependencies on your Azure Virtual Machine.
Run the following commands :

sudo apt update
sudo apt -y upgrade
sudo apt -y install python3-pip
pip3 install flask
Run sudo apt -y install apache2 python3-certbot-apache to install the Apache web server and the certbot-apache plugin.

Apache is a popular open-source web server that is used to host websites and web applications whilst certbot is a tool that can be used to obtain and manage SSL/TLS certificates for websites.

Run sudo certbot --apache to obtain and install an SSL/TLS certificate for the website using the certbot tool and the Apache web server.

Install and Set Up Database Server (MariaDB) :
Install MariaDb database on the Azure virtual Machine:
Run the following commands:
sudo apt -y install mariadb-server mariadb-client libmariadbclient-dev
pip3 install flask_cors mysql-connector-python
sudo mysql
CREATE USER 'web'@'localhost' IDENTIFIED BY 'webPass';
GRANT ALL PRIVILEGES ON *.* to 'web'@'localhost';
Database Configuration: Set up the MariaDB instance.

Run the following commands:
CREATE DATABASE BookStore;
USE BookStore;
CREATE TABLE users (
userID INT NOT NULL AUTO_INCREMENT,
userName VARCHAR(50),
userType ENUM('Supplier', 'Customer') NOT NULL,
password VARCHAR(255),
PRIMARY KEY(userID));

CREATE TABLE Book (
bookID INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
bookName VARCHAR(50) NOT NULL,
price DECIMAL(10, 2) NOT NULL,
rating float,
quantity DECIMAL(10, 2) NOT NULL,
bookDescription VARCHAR(500),
userID INT,
FOREIGN KEY (userID) REFERENCES users(userID)
);

Prepare the Flask Application:
Run sudo cp /etc/letsencrypt/live/<hostname>/cert.pem .
This command copies the certificate file (cert.pem) from the /etc/letsencrypt/live/<hostname> directory to the current working directory.

Run sudo cp /etc/letsencrypt/live/<hostname>/privkey.pem .

This command copies the private key file (privkey.pem) from the /etc/letsencrypt/live/<hostname> directory to the current working directory.

Run sudo chown `whoami` *.pem
This command changes the ownership of the cert.pem and privkey.pem files to the current
user (whoami).

The reason for copying the certificate and private key files to the current working directory is that they are typically needed by the web server in order to serve HTTPS requests. By copying the files to the current working directory, they will be easily accessible to the web server.
The reason for changing the ownership of the cert.pem and privkey.pem files to the current user is that they should only be readable and writable by the user who runs the web server. This helps to protect them from being accidentally or maliciously modified.

Application Configuration: Update the Flask app configuration to use the production database settings, including the database URL, username and password.
Ensure Database Compatibility: Verify that the Flask app’s database library is compatible with MariaDB.
Test Locally: Verify that your Flask app works as expected on your local machine before deploying it.
Clone Repository: Pull or clone your Flask application’s repository onto your Azure Virtual Machine.
Enable HTTP port 8080:
Go to Networking on the left menu of the Virtual Machine Instance
Click Networking Settings
Click +Create port rule
Select Inbound ports:
Source: Any
Source port ranges: 80
Protocol: TCP
Name: HTTP
Description : Allow incoming web requests
Click Add
