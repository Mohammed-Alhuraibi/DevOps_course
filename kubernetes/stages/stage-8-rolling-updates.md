# Stage 8: Rolling updates

[Kubernetes lesson](../README.md) · [Concepts](../concepts.md) · [← Stage 7](stage-7-ingress.md) · **Stage 8** · [Stage 9 →](stage-9-high-availability.md)

On the VM a new version meant `docker compose up -d` and a few seconds of downtime. Kubernetes
swaps pods one at a time instead: a new pod must be ready before an old one stops. You update the
frontend while a loop keeps calling the site, and watch the version change in the game's footer.

**By the end:** you have rolled the frontend from v1 to v2 and back without a failed request, and
you know why the files say `sleep 15`.

![Rolling updates in four steps: three v1 frontend pods (sha-0902b98); a v2 pod (sha-dcb0790) becomes ready, then a v1 pod stops; the same again; finally three v2 pods; traffic never stops because the Service only sends visitors to ready pods, and the game's footer shows which commit is live; kubectl set image deployment/frontend starts the update and kubectl rollout undo deployment/frontend brings v1 back](../images/slides/k8s-09-rolling-updates.svg)

## 1. Note the version

Why: the footer shows which frontend commit is live, so you can see the update land.

```console
laptop$ kubectl get deployment frontend -o jsonpath='{.spec.template.spec.containers[0].image}'; echo
```

You should see `alhuraibisaeed/bugsquash-frontend:sha-0902b98`, and in your browser at
`http://<your IP>` the footer says **Web 0902b98**.

## 2. Start a traffic loop

Why: proof beats promises. One request per second, and you see the status code of every answer.

Open a second terminal window and run in it (`<your IP>` is the address of `bugsquash-ip`):

```console
laptop$ IP=<your IP>
laptop$ while true; do curl -s -m 5 -o /dev/null -w "%{http_code} " http://$IP/; sleep 1; done
```

You should see a growing line of `200 200 200 …`. Leave it running and go back to the first window.

## 3. Roll out v2

Why: `set image` changes one field of the pod template; Kubernetes sees a new template and replaces
the pods one by one.

```console
laptop$ kubectl set image deployment/frontend frontend=alhuraibisaeed/bugsquash-frontend:sha-dcb0790
laptop$ kubectl rollout status deployment/frontend --timeout=180s
laptop$ kubectl get pods -l app=frontend -o custom-columns=POD:.metadata.name,IMAGE:.spec.containers[0].image
```

You should see (trimmed) the rollout move one pod at a time, then new and old pods side by side:

```text
deployment.apps/frontend image updated
Waiting for deployment "frontend" rollout to finish: 1 out of 3 new replicas have been updated...
Waiting for deployment "frontend" rollout to finish: 2 out of 3 new replicas have been updated...
Waiting for deployment "frontend" rollout to finish: 1 old replicas are pending termination...
deployment "frontend" successfully rolled out
POD                         IMAGE
frontend-7d6d9b888f-4bh9f   alhuraibisaeed/bugsquash-frontend:sha-dcb0790
frontend-7d6d9b888f-brpps   alhuraibisaeed/bugsquash-frontend:sha-dcb0790
frontend-7d6d9b888f-wrmrp   alhuraibisaeed/bugsquash-frontend:sha-dcb0790
frontend-d6d8d8454-w85qg    alhuraibisaeed/bugsquash-frontend:sha-0902b98
```

The last pod is an old one taking its 15-second goodbye. Reload the game: the footer says
**Web dcb0790**. The loop in the second window still shows only `200`.

## 4. Look at the history

Why: every change of the template is a numbered revision, kept so that you can go back.

```console
laptop$ kubectl rollout history deployment/frontend
```

You should see:

```text
deployment.apps/frontend
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
```

## 5. Undo

Why: v2 has a bug? One command brings v1 back, with the same one-by-one swap.

```console
laptop$ kubectl rollout undo deployment/frontend
laptop$ kubectl rollout status deployment/frontend --timeout=180s
```

You should see a warning, then the same rollout as in step 3 (trimmed):

```text
Warning: resource deployments/frontend was previously managed with 'kubectl apply'. Rolling back will not update the kubectl.kubernetes.io/last-applied-configuration annotation, …
deployment.apps/frontend rolled back
deployment "frontend" successfully rolled out
```

The warning is harmless: kubectl reminds you that the cluster and your file may now disagree.
Reload the game: **Web 0902b98** again.

## 6. Make the file the truth again

Why: after `set image` and `undo`, apply the file, so that the cluster and Git agree again (Stage 3).

```console
laptop$ kubectl apply -f manifests/02-frontend-deployment.yaml
```

You should see: `deployment.apps/frontend configured`. Stop the loop in the second window with
**Ctrl+C**, but keep the window open: Stage 9 uses it.

## Why the files say `sleep 15`

The first time we tested this update, the loop lost **7 of 124** requests. Kubernetes did its part:
it told an old pod to stop and, at the same moment, told the load balancer to remove it. But that
news takes a few seconds to reach Google's load balancer, which kept sending visitors to a pod that
was already shutting down. The fix is three lines in the frontend and backend Deployments:

```yaml
          lifecycle:
            preStop:
              exec: { command: ["sleep", "15"] }
```

Before the app is told to stop, it waits 15 seconds, still serving, while the load balancer catches
up. Second test: **520 of 520** requests answered. It is also why old pods linger as `Terminating`
and a rollout takes about a minute.

> [!NOTE]
> **Closing a shop.** First you turn the sign to *Closed*, then you serve the customers who are
> already inside, and only then do you lock the door. Without the pause, the shop locked its door
> while customers were still walking in.

## Checkpoint

- `set image` started a rolling update; `rollout status` and `rollout history` followed it;
  `rollout undo` reversed it.
- New pods are ready before old ones stop, and the 15-second pause lets the load balancer catch up.
- The file and the cluster agree again: `sha-0902b98`.

Next: what if a whole machine dies? [Stage 9: High availability](stage-9-high-availability.md).

<details>
<summary>Going deeper</summary>

- **How many at a time?** The default strategy allows 25% extra pods and 25% missing ones. With 3
  replicas that rounds to one extra pod and none missing: never fewer than 3 ready.
- **In real life** nobody types `set image`: CI writes the new tag into the file and applies it, or
  a GitOps tool does (Stage 10).
- `kubectl rollout undo deployment/frontend --to-revision=1` goes back to a chosen revision.

</details>

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| New pods show `ErrImagePull` or `ImagePullBackOff` | Typo in the tag. The old pods keep serving meanwhile: `kubectl rollout undo deployment/frontend`. |
| The footer still shows the old version | Wait for `successfully rolled out`, then reload with Ctrl+Shift+R. |
| A few `000` or `502` appear during the rollout | The pods run without the pause: `kubectl apply -f manifests/02-frontend-deployment.yaml`, then try again. |
| The loop prints only `000`, from the start | `$IP` is empty in the second window: set it again (step 2). |
