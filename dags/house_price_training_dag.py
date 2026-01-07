from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'manas',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 7),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'house_price_training_pipeline',
    default_args=default_args,
    description='End-to-end MLOps pipeline: ETL -> Training -> Model Registry',
    schedule_interval='@weekly',
    catchup=False,
    tags=['mlops', 'house-price', 'training'],
)

etl_task = BashOperator(
    task_id='run_etl',
    bash_command='cd /opt/mlops && python3 scripts/etl_pipeline.py',
    dag=dag,
)

validate_data_task = BashOperator(
    task_id='validate_data',
    bash_command='''
    if [ ! -f /opt/mlops/data/processed/train.csv ]; then
        echo "Error: train.csv not found"
        exit 1
    fi
    echo "✓ Data validation passed"
    ''',
    dag=dag,
)

train_task = BashOperator(
    task_id='train_model',
    bash_command='cd /opt/mlops && python3 scripts/train_new_experiment.py',
    dag=dag,
)

# Simple success message
success_task = BashOperator(
    task_id='pipeline_success',
    bash_command='echo "✓ Pipeline completed! New model logged to MLflow. Check MLflow UI: http://10.142.0.3:30000"',
    dag=dag,
)

# Remove validate_model task, go straight from train to success
etl_task >> validate_data_task >> train_task >> success_task
