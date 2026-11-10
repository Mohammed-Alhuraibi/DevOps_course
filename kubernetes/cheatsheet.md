# Kubernetes cheat sheet

[Lesson map](README.md) · [← Stage 10](stages/stage-10-https-and-wrap-up.md)

The everyday commands of this lesson, ready to copy. Run them in your laptop's terminal from the
`DevOps_course/kubernetes` folder. Replace `<POD_NAME>` with a name from `kubectl get pods`.
The namespace is already `bugsquash` ([Stage 0, step 6](stages/stage-0-create-the-cluster.md#6-create-the-namespace)).

## Look

```bash
# The nodes and the zone each one is in
kubectl get nodes -L topology.kubernetes.io/zone

# Pods with their IP and node
kubectl get pods -o wide

# Only the pods with one label
kubectl get pods -l app=backend

# Everything of the app at once
kubectl get deployment,service,ingress,pvc

# The full story of one pod; the events at the end come first when something is wrong
kubectl describe pod <POD_NAME>

# What happened lately in the namespace, newest last
kubectl get events --sort-by=.lastTimestamp
```

## Apply

```bash
# Create or update whatever a file describes
kubectl apply -f manifests/02-frontend-deployment.yaml

# The Secret, made from random values, never from a file in Git
kubectl create secret generic bugsquash-secrets \
  --from-literal=POSTGRES_PASSWORD="$(openssl rand -hex 24)" \
  --from-literal=JWT_SECRET="$(openssl rand -hex 32)"

# Make bugsquash the default namespace (no more -n bugsquash)
kubectl config set-context --current --namespace=bugsquash
```

## Debug

```bash
# The output of one pod, or of one pod of a Deployment
kubectl logs <POD_NAME>
kubectl logs deployment/backend --tail=20

# The last 10 minutes of every backend pod, each line marked with its pod
kubectl logs -l app=backend --prefix --since=10m

# A shell inside a pod (exit with: exit)
kubectl exec -it <POD_NAME> -- sh

# Call a Service from inside the cluster (the toolbox pod of Stage 4)
kubectl exec toolbox -- curl -s "http://backend:3000/api/health"

# A private tunnel to a pod: then open http://localhost:8080 (Ctrl+C to stop)
kubectl port-forward pod/<POD_NAME> 8080:8080
```

## Scale and update

```bash
# Change the number of copies right now (the next apply of the file sets it back)
kubectl scale deployment/frontend --replicas=5

# Roll out another image, and follow the rollout
kubectl set image deployment/frontend frontend=alhuraibisaeed/bugsquash-frontend:sha-dcb0790
kubectl rollout status deployment/frontend

# The revisions, and back to the previous one
kubectl rollout history deployment/frontend
kubectl rollout undo deployment/frontend

# Fresh pods with the same template: after a ConfigMap change, or to spread pods again
kubectl rollout restart deployment/backend
```

## Clean up

```bash
# One pod (a Deployment replaces it at once; a lone pod is gone for good)
kubectl delete pod <POD_NAME>

# Whatever a file created
kubectl delete -f manifests/01-pod.yaml

# Everything of the lesson, including the load balancer and the disk
kubectl delete namespace bugsquash
```

## gcloud and the console

```bash
# Connect kubectl to the cluster (copy it from the cluster's Connect button)
gcloud container clusters get-credentials bugsquash --region europe-central2 --project <PROJECT_ID>
```

Everything else is in the console (<https://console.cloud.google.com>):

| You want to | Where |
|-------------|-------|
| create the cluster (**Standard**, see [Stage 0](stages/stage-0-create-the-cluster.md#1-create-the-cluster-in-the-console)) | Kubernetes Engine → Clusters → Create |
| see nodes, pods, Services and the Ingress | Kubernetes Engine → Clusters → bugsquash → Nodes; Kubernetes Engine → Workloads; Kubernetes Engine → Gateways, Services & Ingress |
| reserve or release the static IP | VPC network → IP addresses |
| stop or start a node | Compute Engine → **Instance groups** → the node's `…-grp` → tick the VM → Stop, or Start |
| see the database disk and the load balancer | Compute Engine → Storage → Disks; Network services → Load balancing |
| delete the cluster (after `kubectl delete namespace bugsquash`) | Kubernetes Engine → Clusters → bugsquash → Delete |
