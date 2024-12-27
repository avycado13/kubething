from app.main import bp
from flask import request, jsonify,current_app
from app.models import ApiKey
from app.extensions import scheduler
@bp.route('/add_job', methods=['POST'])
def add_job():
    # Extract job details from the request
    job_name = request.json.get('job_name')
    image = request.json.get('image')
    command = request.json.get('command')
    namespace = request.json.get('namespace', 'default')
    api_key = request.headers.get('X-API-KEY')

    # Extract resource limits from the request
    cpu_limit = request.json.get('cpu_limit', '100m') # Default to 100 milliCPU
    memory_limit = request.json.get('memory_limit', '128Mi') # Default to 128 MiB

    # Define the job spec with resource limits
    job = {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {
            "name": job_name,
            "namespace": namespace
        },
        "spec": {
            "template": {
                "spec": {
                    "containers": [
                        {
                            "name": job_name,
                            "image": image,
                            "command": command,
                            "resources": {
                                "limits": {
                                    "cpu": cpu_limit,
                                    "memory": memory_limit
                                }
                            }
                        }
                    ],
                    "restartPolicy": "Never"
                }
            },
            "backoffLimit": 4
        }
    }

    # Create the job in the cluster
    current_app.v1.create_namespaced_job(namespace=namespace, body=job)

    # Schedule a task to monitor and deduct cost for this job
    scheduler.add_job(id=job_name, func=monitor_and_deduct_cost, args=[job_name, namespace, api_key], trigger='interval', seconds=10)

    return jsonify({"message": f"Job {job_name} created successfully and monitoring started."}), 201

def monitor_and_deduct_cost(job_name, namespace, api_key):
    if job_completed(job_name, namespace):
        cpu_usage, memory_usage = get_pod_metrics(job_name, namespace)
        cost = calculate_cost(cpu_usage, memory_usage)

        key = ApiKey.query.filter_by(api_key=api_key).first()
        if not key.deduct_cost(cost):
            print(f"Insufficient balance to deduct cost for job {job_name}.")
        else:
            print(f"Cost deducted for job {job_name}.")

        # Remove the job from the scheduler once it's completed and cost is deducted
        scheduler.remove_job(job_name)

def job_completed(job_name, namespace):
    job = current_app.v1.read_namespaced_job(name=job_name, namespace=namespace)
    return job.status.succeeded == 1

def get_pod_metrics(pod_name, namespace):
    api_version = 'metrics.k8s.io/v1beta1'
    group = 'metrics.k8s.io'
    metrics_path = f'/apis/{group}/{api_version}/namespaces/{namespace}/pods/{pod_name}'
    metrics = current_app.metrics_api.get_namespaced_custom_object(group, api_version, namespace, 'pods', pod_name)
    cpu_usage = metrics['containers'][0]['usage']['cpu']
    memory_usage = metrics['containers'][0]['usage']['memory']
    return cpu_usage, memory_usage

def calculate_cost(cpu_usage, memory_usage):
    # Define pricing rates
    cpu_rate = current_app.config['CPU_RATE'] # $0.10 per CPU hour
    memory_rate = current_app.config['MEMORY_RATE'] # $0.05 per GB hour

    # Calculate cost
    cost = (cpu_usage * cpu_rate) + (memory_usage * memory_rate)
    return cost