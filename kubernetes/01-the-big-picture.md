# 1. The big picture

[Lesson map](README.md) · [← 0. Create the cluster](00-create-the-cluster.md) · **1. The big picture** · [2. Pods →](02-pods.md)

On one VM *you* are the safety net: when the VM dies, the site dies, and you bring it back by hand.
On a cluster you write down what you want, and Kubernetes keeps it true, day and night. Two slides
explain how; three commands find both halves of the cluster you just rented.

**By the end:** you can name the two halves of a cluster, the brain and the workers, and point at
each of them in your own.

![Why Kubernetes: with Docker Compose on one VM the site dies with the VM, and scaling and updates are done by hand with brief downtime; a Kubernetes cluster spreads pods over three machines, starts a new pod when one dies, scales from 3 to 5 copies with one line and updates one pod at a time; like a thermostat set to 21 degrees, you write replicas: 3 and Kubernetes keeps 3 copies running](images/slides/k8s-01-why-kubernetes.svg)

![The cluster as a restaurant: the control plane is the manager, run by Google on GKE, with the API server as the front desk every request goes through, the scheduler that picks a node for every new pod, the controller manager that keeps reality equal to the plan, and etcd, the notebook with the whole cluster's state; kubectl on your laptop talks only to the API server; three worker nodes are the cooks, each with a kubelet that follows the manager's orders, containerd that runs the containers and kube-proxy that routes Service traffic](images/slides/k8s-02-brain-and-workers.svg)

> [!NOTE]
> **A thermostat.** You don't tell a thermostat "heat for ten minutes"; you set 21 °C and it keeps
> checking and correcting. Kubernetes works the same way: you write *what* you want (three copies),
> and its controllers keep comparing that with reality and fix every difference.

## 1. Meet the workers

Why: each node is an ordinary VM, and its zone label says which data centre it stands in.

```console
cloudshell$ kubectl get nodes -L topology.kubernetes.io/zone
```

You should see one node per zone (`-L` shows a label as an extra column):

```text
NAME                                       STATUS   ROLES    AGE   VERSION               ZONE
gke-bugsquash-default-pool-23acb34b-32v4   Ready    <none>   26s   v1.36.4-gke.2377000   europe-central2-b
gke-bugsquash-default-pool-34ca6972-2bt9   Ready    <none>   26s   v1.36.4-gke.2377000   europe-central2-a
gke-bugsquash-default-pool-7204075e-xh1n   Ready    <none>   25s   v1.36.4-gke.2377000   europe-central2-c
```

These are the cooks. Each runs a kubelet, which takes orders from the control plane, and containerd,
which starts the containers.

## 2. Find the brain

Why: kubectl only ever talks to one thing, the control plane's API server.

```console
cloudshell$ kubectl cluster-info | head -2
```

You should see:

```text
Kubernetes control plane is running at https://34.118.41.149
GLBCDefaultBackend is running at https://34.118.41.149/api/v1/namespaces/kube-system/services/default-http-backend:http/proxy
```

That address is the front desk of the control plane. It is not one of your nodes: it never appears
in `kubectl get nodes`, and you cannot log in to it. Google runs it, with copies in all three zones.

## 3. Peek at Kubernetes' own pods

Why: Kubernetes runs its own helpers (logs, metrics, storage drivers, DNS) as pods too, in the
`kube-system` namespace.

```console
cloudshell$ kubectl get pods -n kube-system | head -12
```

You should see a list like this one (trimmed). On a brand-new cluster many are still starting:

```text
NAME                                                  READY   STATUS            RESTARTS   AGE
autoscaling-metrics-adapter-5748b86b98-4gnmw          0/1     PodInitializing   0          11s
event-exporter-gke-58cbcf9f6-shtsg                    0/2     PodInitializing   0          94s
filestore-node-h57zx                                  0/4     PodInitializing   0          27s
fluentbit-gke-b4pb5                                   0/3     PodInitializing   0          27s
gke-metrics-agent-r7g8r                               3/3     Running           0          27s
```

`-n kube-system` looks into another namespace for this one command; your default stays `bugsquash`.

> [!TIP]
> One of these helpers is the cluster's DNS, which page 4 relies on. On a brand-new cluster it may
> need a minute or two: if a name lookup fails at first, wait a minute and try again.

## Checkpoint

- The control plane decides; the worker nodes run the pods. On GKE, Google runs the control plane.
- Your three nodes are in zones a, b and c.
- You describe what you want; Kubernetes keeps reality equal to it.

Next: the smallest thing Kubernetes runs. [2. Pods](02-pods.md).

<details>
<summary>Going deeper</summary>

- **Nodes are just VMs.** `gcloud compute instances list` shows the three nodes as ordinary Compute
  Engine VMs, like the course VM. Never change them by hand: GKE manages them (page 9 stops one on
  purpose).
- **Every command is an HTTPS request.** Add `-v=6` to any kubectl command, for example
  `kubectl get nodes -v=6`, to see the request it sends to the API server.

</details>

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| A node shows `NotReady` | The cluster is still finishing: wait a minute and run the command again. |
| `The connection to the server localhost:8080 was refused` | kubectl has no cluster: `gcloud container clusters get-credentials bugsquash --region europe-central2`. |
| `kube-system` pods still not `Running` after 5 minutes | `kubectl get events -n kube-system --sort-by=.lastTimestamp \| tail` shows what they are waiting for. |
