source ../bin/activate
mkdir -p logs
echo >> logs/gunicorn.error.log
echo >> logs/gunicorn.access.log
pip install -r requirements.txt || \
   echo "pip install failed, existing..." && exit
export DB_ENGINE="postgresql://blog:#blog@localhost:5432/blog" 
export SECRET_KEY="60d7cbe4086ffefaf3791b62978054"
export PORT=3000
export MAILGUN_DOMAIN='mail.horlarwumhe.me'
export  MAILGUN_SMTP_PASSWORD="b634130ce6cac0143182b9dfaa09a32e-fb87af35-4b1624c0"
export MAILGUN_SMTP_USERNAME='postmaster@mail.horlarwumhe.me'
gunicorn --error-logfile logs/gunicorn.error.log \
       --access-logfile logs/gunicorn.access.log  main:app -D


# rq worker 1>logs/rq.log 2>&1 &

echo "booted........."