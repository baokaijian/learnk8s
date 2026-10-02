# 小白入门：先让一个网站跑起来

先完成一次“部署 → 访问 → 扩容 → 观察恢复 → 排障 → 回滚 → 清理”，再阅读底层原理。一次练习约 45–90 分钟，安装和下载时间另计。这里使用本地 minikube 集群，只需要标准 Kubernetes 资源。

本次已验证清单的 YAML 与内置资源字段，尚未在真实集群运行整套实验。镜像下载、驱动和节点资源问题仍需在你的环境验证。

## 先认识五个概念

| 概念 | 在本实验中的作用 |
|---|---|
| 镜像 / 容器 | 镜像是打包结果，容器是运行中的应用进程 |
| Pod | 容器运行的部署、调度单元，名字和 IP 可能改变 |
| Deployment | 声明需要几个副本，并创建或替换 Pod |
| Service | 通过标签找到后端，提供稳定的访问入口 |
| ConfigMap | 保存非敏感配置；本例保存网页内容 |

关系：`Deployment → ReplicaSet → Pod → nginx 容器`；`Service → 匹配 app=web 的就绪 Pod`；`ConfigMap → 挂载进容器的网页文件`。kubectl 向 API Server 提交对象，后续工作由控制器、调度器和 kubelet 完成。

## 0. 准备自己的实验环境

需要会打开终端、切换目录和编辑文本。YAML 使用空格缩进，不用 Tab。下列命令使用 macOS/Linux 或 Windows WSL 的终端语法；第一次不需要先学 Linux Namespace、etcd 或服务网格。

安装并启动 Docker（或按 minikube 官方文档选择其他受支持驱动），安装 minikube 和 kubectl。建议给本地实验至少 2 核、4 GiB 可用内存；软件及镜像首次下载需要网络。按你的系统查看 [minikube 安装步骤](https://minikube.sigs.k8s.io/docs/start/) 与 [kubectl 安装步骤](https://kubernetes.io/docs/tasks/tools/)。

在**自己的电脑终端**执行；以下 kubectl 命令显式使用实验上下文 `learnk8s`：

```bash
minikube start -p learnk8s --driver=docker --cpus=2 --memory=4096
kubectl --context=learnk8s get nodes
kubectl --context=learnk8s version
```

预期：节点为 `Ready`，可看到客户端与服务端版本。若没有 Docker 驱动，先按官方驱动说明完成环境准备，不继续后续步骤。kubectl 与 API Server 应遵循官方 [版本差异策略](https://kubernetes.io/releases/version-skew-policy/)；客户端通常允许相差一个次版本。

从项目根目录继续，确认能找到 `examples/beginner/app.yaml`。该文件完整包含 Namespace、ConfigMap、Deployment 和 Service，无私有镜像、Secret、PVC 或额外插件依赖。nginx 镜像使用官方发布列表中列出的 `1.31.6-alpine` 标签；这是 **nginx 的版本**，与 Kubernetes 版本无关。标签仍可能变化，生产环境需另行验证并固定摘要。[镜像发布依据](https://github.com/docker-library/official-images/blob/master/library/nginx)。

## 1. 部署并观察结果

```bash
kubectl --context=learnk8s apply -f examples/beginner/app.yaml
kubectl --context=learnk8s -n k8s-lab rollout status deployment/web --timeout=180s
kubectl --context=learnk8s -n k8s-lab get deployment,replicaset,pods,service
kubectl --context=learnk8s -n k8s-lab get endpointslices -l kubernetes.io/service-name=web
```

预期：Deployment 最终为 `2/2`，两个 Pod 都为 `1/1 Running`，Service 类型为 `ClusterIP`，EndpointSlice 中有就绪后端。资源名字中的随机后缀与 IP 每次可能不同。

自测：为什么只创建一个 Deployment，却出现 ReplicaSet 和两个 Pod？`Running` 是否一定表示 `Ready`？若启动没有完成，先做第 5 步的排障，不靠反复删除试运气。

## 2. 从电脑访问网站

在**终端 A**运行，保持进程不退出：

```bash
kubectl --context=learnk8s -n k8s-lab port-forward service/web 8080:80
```

在**终端 B**运行，或用浏览器打开 `http://127.0.0.1:8080`：

```bash
curl http://127.0.0.1:8080
kubectl --context=learnk8s -n k8s-lab logs -l app=web --all-containers=true --tail=20
```

预期：页面包含 `Hello Kubernetes!`，访问日志出现请求。端口已占用时把本地端口改成 `8081:80`。

端口转发会选定一个 Pod，通过 API Server/kubelet 建立调试通道；它不能证明真实 ClusterIP 数据平面和负载均衡已验证。若想验证集群内路径，可选做：

```bash
kubectl --context=learnk8s -n k8s-lab run client --image=busybox:1.36 --restart=Never --command -- sleep 3600
kubectl --context=learnk8s -n k8s-lab wait --for=condition=Ready pod/client --timeout=120s
kubectl --context=learnk8s -n k8s-lab exec client -- wget -qO- http://web
kubectl --context=learnk8s -n k8s-lab delete pod client
```

预期：集群里的 client 能通过 Service 名称获取网页。`port-forward` 是学习和调试入口；真实外部入口以后再学 LoadBalancer 与 Gateway API。官方基础流程可参考 [Hello Minikube](https://kubernetes.io/docs/tutorials/hello-minikube/)。

## 3. 扩容并理解声明式配置

```bash
kubectl --context=learnk8s -n k8s-lab scale deployment/web --replicas=3
kubectl --context=learnk8s -n k8s-lab rollout status deployment/web --timeout=180s
kubectl --context=learnk8s -n k8s-lab get pods -l app=web
```

预期：最终出现三个就绪的 web Pod。再执行原来的 apply：

```bash
kubectl --context=learnk8s apply -f examples/beginner/app.yaml
kubectl --context=learnk8s -n k8s-lab rollout status deployment/web --timeout=180s
```

预期：回到文件声明的两个副本。解释：手动 scale 改了在线对象，文件仍写 `replicas: 2`。长期维护时把期望状态放进文件；启用 HPA 时另需处理 replicas 字段的管理权。

## 4. 删除一个 Pod，观察控制器补回

```bash
kubectl --context=learnk8s -n k8s-lab get pods -l app=web
```

从输出中选**一个**完整 Pod 名，替换下面的 `POD_NAME`：

```bash
kubectl --context=learnk8s -n k8s-lab delete pod POD_NAME
kubectl --context=learnk8s -n k8s-lab get pods -l app=web -w
```

预期：旧 Pod 终止，新名字的 Pod 出现，最终仍有两个就绪副本。按 `Ctrl+C` 结束观察。若被删除的是 port-forward 选中的 Pod，转发会断开，回到第 2 步重启它。

这验证了控制器补副本；它没有验证节点故障、高可用、数据库恢复或多可用区容灾。

## 5. 制造一个镜像错误，练习找证据

仅在本实验 Deployment 中设置一个不存在的标签：

```bash
kubectl --context=learnk8s -n k8s-lab set image deployment/web nginx=nginx:learnk8s-does-not-exist
kubectl --context=learnk8s -n k8s-lab get pods -l app=web
```

新 Pod 最终可能显示 `ErrImagePull` 或 `ImagePullBackOff`。选新建的异常 Pod 名替换 `POD_NAME`：

```bash
kubectl --context=learnk8s -n k8s-lab describe pod POD_NAME
kubectl --context=learnk8s -n k8s-lab get events --sort-by=.metadata.creationTimestamp
kubectl --context=learnk8s -n k8s-lab get deployment/web -o yaml
```

观察 Events 的拉取失败原因，以及 Deployment 中错误的镜像标签。由于设置了 `maxUnavailable: 0`，原来的健康副本通常会保留；这需要节点还有创建额外 Pod 的资源。

| 现象 | 第一份证据 | 常见方向 |
|---|---|---|
| Pending | describe 的 Events | 资源、调度条件或 PVC |
| ImagePullBackOff | describe 的拉取错误 | 标签、仓库网络或认证 |
| CrashLoopBackOff | `logs POD_NAME --previous` | 程序退出、配置、依赖或 OOM |
| Running 但未 Ready | describe 的探针事件 | 服务未就绪、探针路径或端口 |
| 网页访问失败 | port-forward 输出 / EndpointSlice | 本地端口、选中 Pod 退出、标签与就绪后端 |

不要先删除所有 Pod。对于未成功启动过的容器，`logs` 没有应用日志也是正常现象。

## 6. 回滚并验证恢复

```bash
kubectl --context=learnk8s -n k8s-lab rollout undo deployment/web
kubectl --context=learnk8s -n k8s-lab rollout status deployment/web --timeout=180s
kubectl --context=learnk8s -n k8s-lab get pods -l app=web
kubectl --context=learnk8s -n k8s-lab get deployment/web -o jsonpath='{.spec.template.spec.containers[0].image}'
```

预期：镜像恢复为 `nginx:1.31.6-alpine`，最后为两个就绪副本。重启端口转发后，再次访问网页。这里回滚的是 Deployment 的 Pod 模板，不是整个集群，也不会回滚 ConfigMap 等其他对象。

## 7. 清理并确认完成

先在终端 A 按 `Ctrl+C` 停止端口转发。下面删除的是实验命名空间及其所有资源，确认它只包含本实验内容：

```bash
kubectl --context=learnk8s delete namespace k8s-lab
kubectl --context=learnk8s get namespace k8s-lab
```

预期：第二条命令返回 `NotFound`。本实验不创建持久卷。

保留集群供下次实验可执行 `minikube stop -p learnk8s`；确定不用时执行 `minikube delete -p learnk8s`，这会删除该实验集群。

## 接下来读什么

第一轮：第 8–13 章建立对象与控制循环认知；第 24、28、39 章学习配置、资源和排障，只读基础段落即可。能独立重做本实验后再学 PVC、RBAC、NetworkPolicy。第 1–7、15–23、27–31 章用于深入原理；高可用、升级、服务网格与 Operator 放在最后。

验收标准：能自行解释五个对象的关系，修改副本数并预测结果，区分容器重启和 Pod 替换，依据 Events 找到镜像错误，恢复服务，并清理实验资源。
