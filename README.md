# SPARCS SSO

SPARCS SSO provides integrated login in SPARCS services, such as ARA or OTL.

### Tech

SPARCS SSO uses following program / framework / libraries:
* Python 2.7.x
* Django 1.9.1
* MySQL (or MariaDB)
* Bootstrap
* jQuery


### Installation

```sh
$ virtualenv sso
$ cd sso
$ git clone https://github.com/sparcs-kaist/sparcssso
$ pip install -r requirements.txt
$ mkdir keys
$ echo "{{django_secret}}" >> keys/django_secret
$ echo "{{fb_app_id}}" >> keys/fb_app_id
$ echo "{{fb_app_secret}}" >> keys/fb_app_secret
$ echo "{{tw_app_id}}" >> keys/tw_app_id
$ echo "{{tw_app_secret}}" >> keys/tw_app_secret
$ echo "{{kaist_app_secret}}" >> keys/kaist_app_secret
$ echo "{{kaist_app_admin_id}}" >> keys/kaist_app_admin_id
$ echo "{{kaist_app_admin_pw}}" >> keys/kaist_app_admin_pw
$ python manage.py makemigration core
$ python manage.py migrate
$ python manage.py runserver
```
