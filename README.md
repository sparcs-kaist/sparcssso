# SPARCS SSO

SPARCS SSO provides integrated login in SPARCS services, such as ARA or OTL.

### Developers
* samjo (PM)
* zazang (Developer)
* gogi (Developer)
* pudding (Designer)
* zoonoo (Translator)
* ashe (Translator)


### Tech

SPARCS SSO uses following program / framework / libraries:
* Python 2.7.x
* Django 1.9.1
* MySQL (or MariaDB)
* Bootstrap
* jQuery


### Installation

SPARCS SSO sends some emails to users, so it requires a mail server such as postfix and sendmail.

* Development
```sh
$ pip install -r requirements.txt
$ mkdir keys
$ echo "{{django_secret}}" >> keys/django_secret
$ echo "{{recaptcha_secret}}" >> keys/recaptcha_secret
$ echo "{{fb_app_id}}" >> keys/fb_app_id
$ echo "{{fb_app_secret}}" >> keys/fb_app_secret
$ echo "{{tw_app_id}}" >> keys/tw_app_id
$ echo "{{tw_app_secret}}" >> keys/tw_app_secret
$ python manage.py makemigration core
$ python manage.py migrate
$ python manage.py compilemessage
```

* Deploy
```sh
$ pip install -r requirements.txt
$ mkdir keys
$ echo "{{django_secret}}" >> keys/django_secret
$ echo "{{recaptcha_secret}}" >> keys/recaptcha_secret
$ echo "{{db_pw}}" >> keys/db_pw
$ echo "{{fb_app_id}}" >> keys/fb_app_id
$ echo "{{fb_app_secret}}" >> keys/fb_app_secret
$ echo "{{tw_app_id}}" >> keys/tw_app_id
$ echo "{{tw_app_secret}}" >> keys/tw_app_secret
$ echo "{{kaist_app_secret}}" >> keys/kaist_app_secret
$ echo "{{kaist_app_admin_id}}" >> keys/kaist_app_admin_id
$ echo "{{kaist_app_admin_pw}}" >> keys/kaist_app_admin_pw
$ touch deploy
$ python manage.py makemigration core
$ python manage.py migrate
$ python manage.py compilemessage
```

### Contributing

Welcome to contribute using pull requests! Please follow the rules:
* PEP8 (max-line: 100 character)
