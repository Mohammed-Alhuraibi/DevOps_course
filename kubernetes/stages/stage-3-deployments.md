# Stage 3: Deployments

[Kubernetes lesson](../README.md) · [Concepts](../concepts.md) · [← Stage 2](stage-2-pods.md) · **Stage 3** · [Stage 4 →](stage-4-services.md)

A lone pod dies alone. A Deployment is a promise: "always keep three copies of this pod running".
A controller compares that promise with reality every few seconds and fixes any difference. You
break things on purpose and watch it repair them.

**By the end:** three frontend pods, one per node, that come back when you delete one, and you know
why the file always wins.

![Deployments: the Deployment frontend with replicas: 3 owns a ReplicaSet that owns three pods; when one crashes, the controller starts a new copy, because its control loop compares the desired state, 3 copies from your YAML, with the actual state, 2 running, every few seconds and fixes the difference; kubectl scale deployment frontend --replicas=5 changes the goal to five copies](../images/slides/k8s-04-deployments.svg)

## 1. Apply the Deployment

Why: `replicas: 3` and a pod `template` are the heart of the file. The rest (health probes, limits,
a 15-second pause, a spread rule) comes back on later pages.

```console
laptop$ kubectl apply -f manifests/02-frontend-deployment.yaml
laptop$ kubectl rollout status deployment/frontend --timeout=120s
```

You should see:

```text
deployment.apps/frontend created
Waiting for deployment "frontend" rollout to finish: 0 of 3 updated replicas are available...
Waiting for deployment "frontend" rollout to finish: 1 of 3 updated replicas are available...
Waiting for deployment "frontend" rollout to finish: 2 of 3 updated replicas are available...
deployment "frontend" successfully rolled out
```

## 2. See the three layers

Why: a Deployment owns a ReplicaSet, which owns the pods, and the names show the family tree.

```console
laptop$ kubectl get deployment,replicaset,pods
laptop$ kubectl get pods -o custom-columns=POD:.metadata.name,NODE:.spec.nodeName,STATUS:.status.phase
```

You should see (ours; your names differ):

```text
NAME                       READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/frontend   3/3     3            3           5s

NAME                                 DESIRED   CURRENT   READY   AGE
replicaset.apps/frontend-d6d8d8454   3         3         3       6s

NAME                           READY   STATUS    RESTARTS   AGE
pod/frontend-d6d8d8454-n9pwz   1/1     Running   0          6s
pod/frontend-d6d8d8454-w85qg   1/1     Running   0          6s
pod/frontend-d6d8d8454-zvd9c   1/1     Running   0          6s

POD                        NODE                                       STATUS
frontend-d6d8d8454-n9pwz   gke-bugsquash-default-pool-23acb34b-32v4   Running
frontend-d6d8d8454-w85qg   gke-bugsquash-default-pool-34ca6972-2bt9   Running
frontend-d6d8d8454-zvd9c   gke-bugsquash-default-pool-7204075e-xh1n   Running
```

A pod's name is the Deployment's name, the ReplicaSet's suffix and a random part. One pod landed on
each node, so in each zone: a spread rule at the bottom of the file asks for that (Stage 9).

## 3. Kill a pod

Why: to watch the control loop notice the difference and fix it.

```console
laptop$ kubectl delete pod <POD_NAME> --wait=false
laptop$ sleep 2; kubectl get pods -l app=frontend
```

Use one of **your** pod names from step 2. `--wait=false` returns at once instead of waiting for
the old pod to finish; `-l app=frontend` lists only the pods with that label.

You should see a brand-new pod, 2 seconds old, next to the two survivors:

```text
pod "frontend-d6d8d8454-n9pwz" deleted from bugsquash namespace
NAME                       READY   STATUS    RESTARTS   AGE
frontend-d6d8d8454-n48vx   1/1     Running   0          2s
frontend-d6d8d8454-w85qg   1/1     Running   0          10s
frontend-d6d8d8454-zvd9c   1/1     Running   0          10s
```

The deleted pod may also still be listed as `Terminating` for about 15 seconds: it finishes the
requests it is serving before it stops (Stage 8 explains that pause).

## 4. Scale up

Why: more visitors coming? Change one number.

**Look in the console:** open **Kubernetes Engine → Workloads** first. While you scale, `frontend`
goes from 3 to 5 pods there and, in step 5, back to 3.

```console
laptop$ kubectl scale deployment/frontend --replicas=5
laptop$ kubectl rollout status deployment/frontend --timeout=90s; kubectl get pods -l app=frontend
```

You should see five pods (trimmed):

```text
deployment.apps/frontend scaled
deployment "frontend" successfully rolled out
NAME                       READY   STATUS    RESTARTS   AGE
frontend-d6d8d8454-4mdbc   1/1     Running   0          11s
frontend-d6d8d8454-n48vx   1/1     Running   0          16s
frontend-d6d8d8454-pwfws   1/1     Running   0          11s
frontend-d6d8d8454-w85qg   1/1     Running   0          24s
frontend-d6d8d8454-zvd9c   1/1     Running   0          24s
```

## 5. Apply the file again

Why: the file still says `replicas: 3`. Who wins, your command or the file?

```console
laptop$ kubectl apply -f manifests/02-frontend-deployment.yaml
laptop$ sleep 5; kubectl get pods -l app=frontend
```

You should see `configured` and three pods again:

```text
deployment.apps/frontend configured
NAME                       READY   STATUS    RESTARTS   AGE
frontend-d6d8d8454-n48vx   1/1     Running   0          23s
frontend-d6d8d8454-w85qg   1/1     Running   0          31s
frontend-d6d8d8454-zvd9c   1/1     Running   0          31s
```

If two extra pods still show `Terminating`, that is the 15-second pause again; run the `get` once more.

> [!NOTE]
> **The file is the truth.** `kubectl scale` is a sticky note on the fridge; the file is the recipe
> book, and the next `apply` follows the book. That is why teams change the file in Git rather than
> the cluster: Git then records who changed what, and when.

## Checkpoint

- A Deployment keeps `replicas` pods running and replaces a deleted one (in 2 seconds in our run).
- `kubectl scale` changes the number right now; `kubectl apply -f` puts the file's number back.
- The pods are spread one per node.

Next: three pods with IPs that change all the time. How do you call them? [Stage 4: Services](stage-4-services.md).

<details>
<summary>Going deeper</summary>

- **Why a ReplicaSet in between?** Every version of the pod template gets its own ReplicaSet. That
  is what lets a Deployment update one pod at a time and go back to an old version (Stage 8).
- **The rest of the file:** the probes are Docker's healthcheck ("send visitors?", "restart it?"),
  and `resources` are Compose's limits, the cgroups of the Docker lesson.

</details>

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Error from server (NotFound): pods "frontend-d6d8d8454-n9pwz" not found` | That is our pod's name: copy one from your own `kubectl get pods`. |
| A pod stays `Terminating` for a while | Normal: every frontend pod waits 15 seconds before it stops (Stage 8). |
| A new pod stays `Pending` | `kubectl describe pod <POD_NAME>`: the events say why, usually that no node has room or the spread rule waits for one. |
| `rollout status` times out | `kubectl get pods`, then `kubectl describe pod <POD_NAME>` for the one that isn't `Running`. |
