# 6. Storage and the backend

[Lesson map](README.md) · [← 5. ConfigMaps and Secrets](05-configmaps-and-secrets.md) · **6. Storage and the backend** · [7. Ingress →](07-ingress.md)

Pods are disposable: delete one and its files are gone. Fine for the frontend, fatal for a database.
The fix is the idea behind Docker's volumes: the data lives on a disk outside the pod, and the next
pod plugs into the same disk. Then the backend joins, and the game gets its API.

**By the end:** Postgres runs on a 5 GiB Google disk, three backend pods answer, and a player called
`survivor` outlives the database pod.

![Storage: the deleted postgres pod and its replacement both show the PersistentVolumeClaim postgres-data, 5 GiB, ReadWriteOnce, bound to a PersistentVolume that is a Google Persistent Disk living outside every pod; like a cloakroom, the claim is the ticket, the volume is the coat and any pod with the ticket gets the same coat back; ReadWriteOnce means one node writes at a time, so the database runs as one pod with the Recreate strategy](images/slides/k8s-07-storage.svg)

## 1. Start the database

Why: one file, three objects: a disk claim, one Postgres pod and the Service `postgres` that the
backend calls (`PGHOST`, page 5).

```console
laptop$ kubectl apply -f manifests/05-postgres.yaml
laptop$ kubectl get pvc
```

You should see the three objects, and the claim still `Pending`:

```text
persistentvolumeclaim/postgres-data created
deployment.apps/postgres created
service/postgres created
NAME            STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
postgres-data   Pending                                      standard-rwo   <unset>                 1s
```

`Pending` is on purpose: GKE waits until the pod has a node, then creates the disk in that node's zone.

## 2. Watch the disk appear

Why: the claim ("I need 5 GiB") gets bound to a real Google Persistent Disk.

```console
laptop$ kubectl rollout status deployment/postgres --timeout=180s
laptop$ kubectl get pvc,pv
laptop$ kubectl get pods -l app=postgres -o wide
```

You should see (trimmed) the claim `Bound` to a 5Gi volume, and the node that runs the database:

```text
deployment "postgres" successfully rolled out
NAME                                  STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS
persistentvolumeclaim/postgres-data   Bound    pvc-4306735b-88b3-4d99-81aa-348ea8d8f1e3   5Gi        RWO            standard-rwo

NAME                                                        CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM
persistentvolume/pvc-4306735b-88b3-4d99-81aa-348ea8d8f1e3   5Gi        RWO            Delete           Bound    bugsquash/postgres-data

NAME                        READY   STATUS    RESTARTS   AGE   IP           NODE
postgres-5b5cd498df-jb9nd   1/1     Running   0          24s   10.76.0.11   gke-bugsquash-default-pool-23acb34b-32v4
```

Remember that node: on page 9 it matters where the database lives.

**Look in the console:** **Compute Engine → Storage → Disks** shows the volume as an ordinary 5 GB
disk named `pvc-4306735b-…`, in one zone only: the zone of the database's node.

## 3. Start the backend

Why: three copies of the API, set up by the ConfigMap and the Secret. They keep no data of their
own, so Kubernetes may stop and move them freely.

```console
laptop$ kubectl apply -f manifests/06-backend.yaml
laptop$ kubectl rollout status deployment/backend --timeout=180s
laptop$ kubectl logs deployment/backend --tail=4
```

You should see (trimmed; `logs deployment/backend` picks one of its pods):

```text
deployment.apps/backend created
service/backend created
deployment "backend" successfully rolled out
Found 3 pods, using pod/backend-67499d7d-qkwgs
[server] starting Bug Squash Arena API dcb0790 (NODE_ENV=production)
[db] schema ready (attempt 1/10)
[server] listening on port 3000
```

`schema ready` means the backend found the database through the Service `postgres` and logged in
with the password from the Secret.

## 4. Sign up a survivor

Why: put one real row into the database, from the toolbox, through the Service `backend`.

```console
laptop$ kubectl exec toolbox -- curl -s http://backend:3000/api/health
laptop$ kubectl exec toolbox -- curl -s -H 'Content-Type: application/json' \
          -d '{"username":"survivor","password":"squash-me-123"}' http://backend:3000/api/auth/signup
```

You should see a healthy API (`ok` only when the database answers too) and a new player, id 1:

```text
{"status":"ok","version":"dcb0790"}
{"user":{"id":1,"username":"survivor"}}
```

## 5. Delete the database pod, then log in again

Why: the moment of truth. If the data lived inside the pod, `survivor` would die with it.

```console
laptop$ kubectl delete pod -l app=postgres
laptop$ kubectl rollout status deployment/postgres --timeout=180s; kubectl get pods -l app=postgres
laptop$ kubectl exec toolbox -- curl -s -H 'Content-Type: application/json' \
          -d '{"username":"survivor","password":"squash-me-123"}' http://backend:3000/api/auth/login
```

You should see a new pod (new name) running a few seconds later, and the same player, still id 1:

```text
pod "postgres-5b5cd498df-jb9nd" deleted from bugsquash namespace
deployment "postgres" successfully rolled out
NAME                        READY   STATUS    RESTARTS   AGE
postgres-5b5cd498df-tlpds   1/1     Running   0          4s
{"user":{"id":1,"username":"survivor"}}
```

The new pod showed the same ticket, `postgres-data`, and got the same disk back.

Meanwhile the API is honest: one `/api/health` call returned `503` in our run. The readiness probe
uses that endpoint, so a longer outage would make Kubernetes stop sending visitors to the backend.

> [!NOTE]
> **A cloakroom.** The claim `postgres-data` is your ticket ("a 5 GiB disk, please"); the volume is
> the coat, a real disk Google keeps for you. Any pod with the ticket gets the same coat back. Only
> one node may write to it (`ReadWriteOnce`): hence one database pod, and `strategy: Recreate`.

## Checkpoint

- `postgres-data` is `Bound` to a 5Gi Google disk, and Postgres keeps its data there.
- Three backend pods run, and `/api/health` answers `ok`.
- `survivor` could log in after the database pod was replaced.

Next: everything works, but only inside the cluster. Time for a public door: [7. Ingress](07-ingress.md).

<details>
<summary>Going deeper</summary>

- `RECLAIM POLICY: Delete`: delete the claim and Google deletes the disk, data included. The cleanup
  on page 10 relies on that.

</details>

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| The claim stays `Pending` after the pod has a node | `kubectl describe pvc postgres-data` shows why; a disk quota (`SSD_TOTAL_GB`) is the usual cause. |
| Backend pods stay `0/1`, their logs mention `password authentication failed` | The Secret was recreated after Postgres first started, and Postgres keeps its first password. `kubectl delete deployment postgres`, `kubectl delete pvc postgres-data` (erases the data), apply `05-postgres.yaml` again. |
| `{"error":"That username is already taken"}` | You signed up before: go on with step 5. |
| `/api/health` returns `503` for more than a minute | `kubectl get pods -l app=postgres`, then `kubectl logs deployment/postgres`. |
| `pods "toolbox" not found` | Create it: [page 4, step 3](04-services.md#3-start-a-toolbox-pod). |
