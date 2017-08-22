# Cloud Flare Dynamic DNS Playbook

A basic Ansible playbook to update a DNS record with Cloud Flare
after determining the public IP address.  

A great way of doing your own dynamic DNS updates if you don't have
a static IP address assigned to your endpoint/node.

John Imison <john+github@imison.net>

## Description

This playbook is set to run against localhost and gather no facts.

We use the ipinfoio_facts module to query the http://ipinfo.io/ site
which returns some useful information to us, but, most importantly the
IP address your query originated.  

The we use the cloudflare_dns ansible module to iterate over a number
of items (our domains) and set the DNS A record.  In this example case, 
the DNS A record for mail.


## Use cases

Hosting your own email/web/other services at home but don't have
a static IP address.


## Usage

* Ensure you have a Cloud Flare account and a domain associated 
* Ensure you update the variables in the playbook yml file

```
  vars:
    cf_api_token: 'CF API token under My Profile.. API key'
    cf_email: 'Cloud Flare email address'
```

Then, simply run with:

```bash
ansible-playbook cf_dydns_update.yml
```

If you want it updating on a regular basis, put it into a crontab.


## Caveat

If you're behind a proxy server, the IP address returned maybe that
of another system and useless for dynamic dns update purposes.


## Motivation

Some years ago I wrote my first python script to update my cloudflare
domain DNS records for me.  It was a great task to cut my teeth on
with python.

I've included the original code in the old directory as a comparison
against the 30 line (or less) ansible yml file.

Please no hate mail,  I wrote this old script without care for PEP8.
Pylint graciously gives almost 1/10. 

```
Your code has been rated at 0.74/10
```
