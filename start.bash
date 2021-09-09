source ../bin/activate
pip install -r requirements.txt

export DB_ENGINE="postgresql://blog:#blog@localhost:5432/blog" 
export SECRET_KEY="60d7cbe4086ffefaf3791b62978054"

gunicorn --error-logfile logs/gunicorn.error.log \
       --access-logfile logs/gunicorn.access.log  main:app -D


rq worker 1>blog/logs/rq.log 2>&1 &

echo "booted........."