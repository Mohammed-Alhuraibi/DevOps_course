# 9. High availability

[Lesson map](README.md) · [← 8. Rolling updates](08-rolling-updates.md) · **9. High availability** · [10. HTTPS and wrap-up →](10-https-and-wrap-up.md)

This is the demo the whole lesson builds up to. The game runs in three zones; now one machine is
switched off in the middle of the class while a loop keeps calling the API. Kubernetes and Google's
load balancer have one job: make sure visitors barely notice.

**By the end:** you have stopped a node, counted the failed requests (a handful, all in the first
seconds), brought the node back and spread the pods out again.

![High availability: frontend and backend pods are spread over zones a, b and c behind the Google load balancer, which sends visitors only to ready pods; the instructor stops the node in zone b and, after about 30 seconds, Kubernetes re-creates its two pods on the nodes in zones a and c; the control plane is replicated by Google in all three zones; the honest weak spot is the single Postgres pod with its disk in one zone, so stop a node in another zone, and use Cloud SQL in production](images/slides/k8s-10-high-availability.svg)

## 1. Check the spread

Why: high availability starts before the failure, with one frontend and one backend in every zone.

```console
cloudshell$ kubectl get nodes -L topology.kubernetes.io/zone
cloudshell$ kubectl get pods -o wide -l 'app in (frontend,backend,postgres)' | awk '{print $1, $3, $7}' | column -t
```

The `awk` keeps three columns: name, status and node. You should see (ours, just before the demo;
trimmed) one frontend and one backend on every node:

```text
NAME                                       STATUS   ROLES    AGE   VERSION               ZONE
gke-bugsquash-default-pool-23acb34b-32v4   Ready    <none>   19m   v1.36.4-gke.2377000   europe-central2-b
gke-bugsquash-default-pool-34ca6972-2bt9   Ready    <none>   19m   v1.36.4-gke.2377000   europe-central2-a
gke-bugsquash-default-pool-7204075e-xh1n   Ready    <none>   19m   v1.36.4-gke.2377000   europe-central2-c
NAME                       STATUS   NODE
backend-54bfb9bb75-4n9sl   Running  gke-bugsquash-default-pool-34ca6972-2bt9
backend-54bfb9bb75-9nzmp   Running  gke-bugsquash-default-pool-7204075e-xh1n
backend-54bfb9bb75-klb6b   Running  gke-bugsquash-default-pool-23acb34b-32v4
frontend-7c48b57587-hh2js  Running  gke-bugsquash-default-pool-7204075e-xh1n
frontend-7c48b57587-p64gt  Running  gke-bugsquash-default-pool-34ca6972-2bt9
frontend-7c48b57587-wk745  Running  gke-bugsquash-default-pool-23acb34b-32v4
postgres-5b5cd498df-tlpds  Running  gke-bugsquash-default-pool-23acb34b-32v4
```

That spread is a rule in the files (`topologySpreadConstraints`): zones may differ by at most one
pod, and `DoNotSchedule` makes it a rule, not a wish (with the soft version, a few updates later zone
a had no pods at all). `nodeTaintsPolicy: Honor` leaves broken nodes out, so pods can move off them.

## 2. Find the database's zone

Why: the database is one pod on a disk that lives in one zone (page 6). Stop *its* node and the API
has to wait; stop any other and nobody should notice.

```console
cloudshell$ kubectl get pod -l app=postgres -o wide
```

You should see one pod and its `NODE`. Ours, `postgres-5b5cd498df-tlpds`, ran on
`gke-bugsquash-default-pool-23acb34b-32v4`, which step 1 shows in zone b, so we stopped the node in
**zone a**. Choose a node in another zone than your database, and note its name and zone: the next
steps call them `<NODE>` and `<ZONE>`.

## 3. Start the traffic loop

Why: this time call the API, which needs the whole chain: load balancer, backend and database.

In the second Cloud Shell tab (page 8; **+** opens a new one):

```console
cloudshell$ IP=$(gcloud compute addresses describe bugsquash-ip --global --format='value(address)')
cloudshell$ while true; do curl -s -m 5 -o /dev/null -w "%{http_code} " http://$IP/api/scores/leaderboard; sleep 1; done
```

You should see `200 200 200 …` (the instructor loops on `http://k8s.gulfheight.com`). Keep the game
open in your browser, too.

## 4. Stop a node

Why: a node is a VM, and stopping it is the closest thing to a power cut in one data centre.

```console
cloudshell$ gcloud compute instances stop <NODE> --zone <ZONE>
```

It takes about 2 minutes (1m47s for us): watch the loop in the second tab meanwhile. You should see
(ours):

```text
Updated [https://compute.googleapis.com/compute/v1/projects/<PROJECT_ID>/zones/europe-central2-a/instances/gke-bugsquash-default-pool-34ca6972-2bt9].
```

## 5. Watch Kubernetes react

Why: Kubernetes marks the silent node `NotReady` and, 30 seconds later (the `tolerations` at the end
of the files), re-creates its pods on the nodes that are left.

```console
cloudshell$ kubectl get nodes -L topology.kubernetes.io/zone
cloudshell$ kubectl get pods -o wide -l 'app in (frontend,backend,postgres)' | awk '{print $1, $3, $7}' | column -t
```

Run the second command a few times. You should see the node `NotReady`, its two pods `Terminating`,
their replacements already `Running` elsewhere (trimmed), and a little later only the replacements:

```text
gke-bugsquash-default-pool-34ca6972-2bt9   NotReady   <none>   23m   v1.36.4-gke.2377000   europe-central2-a
backend-54bfb9bb75-4n9sl   Terminating  gke-bugsquash-default-pool-34ca6972-2bt9
backend-54bfb9bb75-zxks8   Running      gke-bugsquash-default-pool-7204075e-xh1n
frontend-7c48b57587-mgdxs  Running      gke-bugsquash-default-pool-7204075e-xh1n
frontend-7c48b57587-p64gt  Terminating  gke-bugsquash-default-pool-34ca6972-2bt9
postgres-5b5cd498df-tlpds  Running      gke-bugsquash-default-pool-23acb34b-32v4
```

Now stop the loop (**Ctrl+C**) and read it. Ours: **5 of 446** requests failed (`000`, no answer),
all within about 11 seconds as the node went down, sent there before the load balancer's health
checks noticed. After that, 100% were answered by the other two zones; the game kept working.

## 6. Bring the node back and spread again

Why: a returning node comes back empty. Kubernetes places pods only when it creates them; it never
moves running pods back by itself.

```console
cloudshell$ gcloud compute instances start <NODE> --zone <ZONE>
cloudshell$ kubectl get nodes -L topology.kubernetes.io/zone
cloudshell$ kubectl rollout restart deployment/frontend deployment/backend
```

Repeat `get nodes` until all three are `Ready`, about a minute after the start. You should see (trimmed):

```text
Instance external IP is 34.116.181.55
gke-bugsquash-default-pool-34ca6972-2bt9   Ready    <none>   3m8s   v1.36.4-gke.2377000   europe-central2-a
deployment.apps/frontend restarted
deployment.apps/backend restarted
```

`rollout restart` is a rolling update with nothing changed but fresh pods, and the spread rule puts
them one per zone again: check with step 1's second command.

## What about the control plane?

"Can we switch off the master too?" Not on GKE: Google runs the control plane, and you can't even
see its machines. In a regional cluster Google keeps copies of it in all three zones, so it survives
a zone outage too. And while it is unreachable the app keeps serving (kubelets keep their pods, the
load balancer keeps sending visitors); you just can't change anything, like cooks who keep cooking
the current orders while the manager is out.

## The honest weak spot

One Postgres pod, on one disk, in one zone. Stop *that* node and the API fails until the node is
back, because a zonal disk can't follow its pod to another zone. Production uses a database that
copies itself across zones: Cloud SQL, or a replicated database.

## Checkpoint

- A hard spread rule keeps one frontend and one backend in every zone.
- Losing a node cost 5 of 446 requests, all in the first ~11 seconds; Kubernetes re-created its pods
  elsewhere, and `rollout restart` spread them again after it returned.
- Google runs the control plane in all three zones; the single database is the weak spot.

Next: the padlock, then cleanup. [10. HTTPS and wrap-up](10-https-and-wrap-up.md).

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| The loop shows only errors (`502`, `503`) after the stop | You stopped the database's node: start it again (step 6); the API recovers about a minute later. |
| Pods on the stopped node still show `Running` | Kubernetes needs about a minute to notice the node, then waits 30 seconds: run the command again. |
| Replacement pods stay `Pending` | The other nodes are full: `kubectl describe pod <POD_NAME>`. They start once the node is back. |
| `kubectl exec toolbox` fails after the demo | The toolbox lived on that node, and a lone pod is never replaced (page 2): `kubectl delete pod toolbox`, then [page 4, step 3](04-services.md#3-start-a-toolbox-pod). |
| `gcloud … stop`: `The resource … was not found` | Wrong zone for that node: use the zone from step 1. |
