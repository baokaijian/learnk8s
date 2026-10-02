# Kubernetes 教程内容核查与新手优化建议

核查日期：2026-10-02。结论：原稿覆盖面较全，但存在会建立错误认知的原理解释，以及会导致复制失败或误操作的示例。已在 `index.html` 中订正确认的问题，补充官方依据和示例前置条件；新增入门练习，调整 README 的学习入口与功能说明。

## 核查范围与版本依据

浏览了 [在线教程](https://baokaijian.github.io/learnk8s/)，重新克隆 [源仓库](https://github.com/baokaijian/learnk8s)，克隆基线为 `c220715fc4c5fe7819dc197d07203043b41b04c8`。远端跟踪文件只有 `.gitignore`、`README.md`、`index.html`；已将缺失的 HTML 从完整克隆恢复至当前工作区，保留现有 Git 历史。

正文核查覆盖导论、43 章和 4 个附录；扫描原稿全部 254 个代码块，并检查文字、表格、图中文字与配置片段之间的一致性。本地 `.workbuddy` 记录仅作项目背景，`.DS_Store` 和 Git 内部数据不含教学内容。

依据以 Kubernetes 官方文档与公开源码为主，涉及 Linux、Docker、etcd、Gateway API、Cilium、gVisor 和 Istio 时采用各项目官方资料。静态字段检查使用 [Kubernetes v1.34.0 OpenAPI](https://github.com/kubernetes/kubernetes/blob/v1.34.0/api/openapi-spec/swagger.json) 作为可复现基线；这不代表最新发布版、仍受支持的版本列表或全部功能的最低版本。旧版本号保留为历史示意，并明确要求按目标版本核对。

“与官方一致”需带适用条件：插件、自定义资源、云平台、内核和特性门控各有版本边界。本次没有搭建集群逐一运行所有示例，不能将静态通过表述为全书生产验证通过。

## 已订正的主要问题

以下按问题归类，重复出现在小结、图示或附录的同类说法一并核对。

| 位置 | 原稿问题 | 订正及意义 | 官方依据 |
|---|---|---|---|
| 导论 / README | 承诺无需外部资料即可掌握，所有 YAML 可直接运行 | 区分完整清单、合并片段、占位模板、伪代码及插件配置；先完成入门实验 | [Kubernetes 基础教程](https://kubernetes.io/docs/tutorials/kubernetes-basics/) |
| 1 / 26 / 37 | 把 gVisor 与 Kata 都解释成每 Pod 独立 Linux 内核 | 区分 Kata 的 guest 内核与 gVisor Sentry 用户态内核；修正图示 | [gVisor 架构](https://gvisor.dev/docs/architecture_guide/intro/) |
| 2 | 单线程同时占用两核；memory.events.low 含义错误 | 改为多线程/进程；low 表示保护范围内仍发生回收，max 不等同已经 OOM；区分终止原因与 Pod phase | [Linux cgroup v2](https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html) |
| 3 / 5 | 语义化标签被当作不可变；COPY 被说成使之前依赖层失效 | 标签仍可变，摘要固定内容；COPY 只影响自身与后续缓存步骤 | [镜像标识](https://kubernetes.io/docs/concepts/containers/images/)、[Docker 缓存](https://docs.docker.com/build/cache/invalidation/) |
| 4 / 6 | 数据库网络示例缺初始化密码；运行中卷 tar 被当作数据库备份；emptyDir 与容器可写层混淆 | 补演示密码与镜像前置条件；标注数据库一致性要求；emptyDir 随 Pod 存在，容器重启可保留 | [PostgreSQL 官方镜像说明](https://github.com/docker-library/docs/tree/master/postgres)、[卷生命周期](https://kubernetes.io/docs/concepts/storage/volumes/) |
| 7 / 9 | runc“几十行”；etcd 存所有数据；全部组件只与 apiserver 通信；etcd 必须奇数成员 | 修正运行时规模与通信边界；应用数据另行备份；偶数成员合法但通常无容错收益 | [组件](https://kubernetes.io/docs/concepts/overview/components/)、[etcd FAQ](https://etcd.io/docs/v3.6/faq/) |
| 9 / 17 | IPVS“已移除”；eBPF“性能最佳” | IPVS 自 v1.35 弃用，弃用不等于移除；性能取决于实现、规模和工作负载 | [Service 代理实现](https://kubernetes.io/docs/reference/networking/virtual-ips/) |
| 9 / 31 | Metrics Server 内置；缺少它所有 HPA 都不能工作 | 资源指标通常依赖另装/预装的 Metrics Server；自定义/外部指标使用其他适配器 | [HPA 指标](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/) |
| 10 | 多个 matchExpressions 可实现跨键 OR；Service selector 使用 LabelSelector 结构 | 所有条件 AND；同一 In 的 values 可选其一；Service selector 使用简单键值映射 | [标签选择器](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/) |
| 10 / A | SSA 保证 HPA 不被覆盖；默认加 force-conflicts | Apply 的冲突检测不覆盖全部 Update/Patch 语义；HPA 的 replicas 字段需移交；强制接管需明确目的 | [SSA](https://kubernetes.io/docs/reference/using-api/server-side-apply/) |
| 11 / B | 主容器未挂载日志卷、只读根目录还写 /tmp；探针同一 YAML 重复键；preStop 无限等文件删除 | 补共享日志与临时卷；拆开探针替代片段；停止 hook 返回后才发 TERM，不能占满宽限期 | [Pod 生命周期](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)、[探针](https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/) |
| 11 / 12 / B | Running 等于正常；裸 Pod 完全不会自愈；原生 sidecar 启动等于就绪 | 区分 Running、Ready、容器重启与 Pod 替换；sidecar 的 started、startupProbe、readinessProbe 各有语义 | [生命周期](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)、[原生 sidecar](https://kubernetes.io/docs/concepts/workloads/pods/sidecar-containers/) |
| 12.2 | minReadySeconds 是缩容保留时间、v1.33 新稳定能力 | 它是新 Pod 持续就绪后计为 Available 的时间；progressDeadline 超时不自动回滚 | [Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) |
| 12 / 23 / B.5 | StatefulSet PVC 永不自动删除；数据库三副本隐含高可用 | PVC 默认 Retain，可配置 Delete 策略；独立数据库副本不会自动复制；补 B.5 Headless Service 与密码 Secret 引用 | [StatefulSet](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/) |
| 13 / 15 / 17 / D | ClusterIP 绝不绑定接口、绝不能 ping；每个包重走 NAT 全规则；只关注本节点 EndpointSlice | IPVS 可使用 dummy 接口；服务可用性应验证实际端口；区分新连接 NAT 与 conntrack，需汇总跨节点后端 | [虚拟 IP](https://kubernetes.io/docs/reference/networking/virtual-ips/)、[EndpointSlice](https://kubernetes.io/docs/concepts/services-networking/endpoint-slices/) |
| 14 / 18 | default 可删除；Pod DNS 要手动创建；nameserver 查询与 NodeLocal 工作路径过度概括 | 标注默认准入保护、DNS 插件模式与解析器差异；NodeLocal 使用节点 DNS 网络端点 | [NamespaceLifecycle 源码](https://github.com/kubernetes/apiserver/blob/master/pkg/admission/plugin/namespace/lifecycle/admission.go)、[DNS](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/)、[NodeLocal](https://kubernetes.io/docs/tasks/administer-cluster/nodelocaldns/) |
| 19 | HTTP listener 自动 HTTPS 重定向；所有 Gateway API 路由一样成熟 | 补 RequestRedirect HTTPRoute、命名空间标签要求；区分 Standard/Experimental 与控制器支持能力 | [重定向](https://gateway-api.sigs.k8s.io/guides/user-guides/http-redirect-rewrite/)、[API 通道](https://gateway-api.sigs.k8s.io/guides/getting-started/introduction/) |
| 20.6 | Cilium 示例含无效 PostgreSQL L7Parser 与省略号 | 保留 HTTP L7 与数据库 TCP 端口授权，明确 TCP 允许不等于 SQL 语句授权 | [Cilium 策略语法](https://docs.cilium.io/en/stable/security/policy/language/) |
| 22 / 39 / B.7 | RWX 自动满足 RWO；同节点共享 RWO 必然损坏文件系统；NFS PV 与 EBS PVC 像一组 | 访问模式必须显式匹配；风险在应用并发写语义；拆分静态 NFS 与动态 EBS 方案 | [持久卷](https://kubernetes.io/docs/concepts/storage/persistent-volumes/) |
| 23 | VolumeSnapshot 自带 pre-backup hook；崩溃一致快照承诺文件系统不损坏 | API 没有该 hook；一致性需应用/备份工具协调，恢复结果需演练 | [卷快照](https://kubernetes.io/docs/concepts/storage/volume-snapshots/) |
| 24 | ConfigMap 一分钟内一定更新；Secret 永不落盘；stringData 被普遍推荐 | 同步延迟取决于 kubelet/watch 缓存；补操作系统/swap 条件和 SSA 的 stringData 限制 | [ConfigMap](https://kubernetes.io/docs/concepts/configuration/configmap/)、[Secret](https://kubernetes.io/docs/concepts/configuration/secret/) |
| 25 / 26 / B.11 | ABAC 已废弃；system:masters 不被审计；create binding/CSIDriver 直接拿 root；baseline 可允许 hostPath | 修正授权、审计与提权前提；hostPath 禁止；区分 Pod 与容器 securityContext，移除旧 PSP 字段建议 | [授权](https://kubernetes.io/docs/reference/access-authn-authz/authorization/)、[RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)、[安全标准](https://kubernetes.io/docs/concepts/security/pod-security-standards/) |
| 27 / 29 | 并发 scheduling cycle；Reserve 在打分前；minDomains 不足一律禁止；手工 Pod 无默认容忍；反亲和性必与 CA 死锁 | 修正调度阶段、skew 算法、默认准入容忍与扩节点解决 hostname 约束的条件 | [调度框架](https://kubernetes.io/docs/concepts/scheduling-eviction/scheduling-framework/)、[拓扑分布](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/)、[污点容忍](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/) |
| 28 / 38 | Burstable OOM 公式错误；request 越接近 limit 分数越高；QoS 构成绝对驱逐顺序 | 使用 kubelet 的内存 request/节点容量调整公式，区分 cgroup OOM、节点 OOM 与 kubelet 驱逐；删除错误因果结论 | [节点驱逐与 OOM](https://kubernetes.io/docs/concepts/scheduling-eviction/node-pressure-eviction/) |
| 30 / B.10 | PDB 强制保护抢占、rollout；单副本配置 PDB 无意义；drain 脚本续行后加注释 | PDB 约束 Eviction API；抢占仅尽力避开违反，rollout 有自身策略；单副本保护会阻塞维护；修复 shell 续行 | [中断预算](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/)、[抢占](https://kubernetes.io/docs/concepts/scheduling-eviction/pod-priority-preemption/) |
| 31 | 所有 HPA 计算都必须有 requests；所有 Pending 均可加节点解决；VPA 只开门控即可原地更新 | Utilization 与 AverageValue/Value 区分；CA 需可扩节点组和可满足约束；VPA 需组件与集群版本兼容 | [HPA](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)、[VPA](https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler) |
| 33 / 39 | containerd 下载参数当日志轮转；文件日志无法被采集；PromQL 混标为 shell | 改为 kubelet containerLogMaxSize/Files；区分 kubectl logs 与文件采集；重新标注混合示意 | [日志架构](https://kubernetes.io/docs/concepts/cluster-administration/logging/) |
| 35 / 36 | etcdctl status/restore；备份脚本接着执行恢复；无失败保护；升级通配旧版本包 | 改 etcdutl，备份失败即停并分离恢复说明；补 watch revision 注意事项；升级改为按 OS/版本官方步骤执行的示意 | [etcd 恢复](https://etcd.io/docs/v3.6/op-guide/recovery/)、[kubeadm 升级](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/) |
| 37 | 配额变更不重新统计；任意注解可绕过 Enforce | 配额重新统计但不驱逐既有对象；PSA 的豁免不是任意注解 | [ResourceQuota](https://kubernetes.io/docs/concepts/policy/resource-quotas/)、[PSA](https://kubernetes.io/docs/concepts/security/pod-security-admission/) |
| 41 | ALLOW 必须先建空策略且依赖顺序；探针都绕开代理；启动等待解决 Job 退出 | 修正 ALLOW 匹配与默认拒绝；说明 istio-agent 探针改写；启动等待不负责退出 | [Istio 授权](https://istio.io/latest/docs/reference/config/security/authorization-policy/)、[探针改写](https://istio.io/latest/docs/ops/configuration/mesh/app-health-check/) |
| 41.1 / 43 / A | 重复 http；Go &currentDeploy 被 HTML 实体吞掉；status 自动只允许控制器写；旧 kubectl 参数及跨命名空间删除错误 | 拆分片段、修复 HTML 转义、说明 RBAC 管写入权限、修正命令；删除 Evicted 先预览并保留 namespace | [自定义资源](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/)、[kubectl](https://kubernetes.io/docs/reference/kubectl/) |

原稿关于 Ingress NGINX 在 2026 年 3 月退役的说明有官方公告支持，予以保留并增加来源。退役的是该控制器项目，不等于 Kubernetes Ingress API 被移除。[官方退役公告](https://kubernetes.io/blog/2025/11/11/ingress-nginx-retirement/)。

## 新手教学优化

当前材料适合系统查阅，但对零基础读者，Linux 原理开篇、生产级大清单和大量插件容易同时引入太多新概念。建议按以下顺序改进。

| 优先级 | 建议 | 本次状态 / 验收方式 |
|---|---|---|
| 高 | 先获得一次完整实践，再补原理 | 已新增 [入门实验](./BEGINNER_GUIDE.md) 与 [app.yaml](./examples/beginner/app.yaml)：部署、访问、扩容、观察恢复、镜像故障、回滚、清理 |
| 高 | 每个实验写前置条件、在哪里执行、预期输出、失败怎么查、如何清理 | 入门实验已落实；正文复杂示例补关键前置条件，其余章节后续按统一模板扩展 |
| 高 | 区分可直接运行与解释用片段 | 已调整导论/附录说明，修复重复字段和错误占位；建议后续逐块添加“完整资源 / 片段 / 伪代码 / 插件配置”视觉标签 |
| 高 | 明确版本边界，避免“全部最新、全部稳定”的印象 | 已注明核查日期、静态基线和历史版本；后续维护单独的实测版本矩阵（Kubernetes、插件、镜像、内核） |
| 中 | 用同一个应用贯穿后续练习 | 先延续 web 实验加入 ConfigMap 更新、Secret、PVC、RBAC、NetworkPolicy、HPA；每轮只引入一类新能力 |
| 中 | 把“背定义”变成“预测 → 操作 → 观察 → 解释” | 入门实验已有自测与故障注入；建议每章加 2–3 个问题并提供答案解析 |
| 中 | 降低翻阅成本 | 已实现标题和正文的章节搜索；后续可增加命中片段/高亮、阅读进度保存和独立章节页 |
| 中 | 把教学清单放进 examples，持续实测 | 已新增 YAML 静态检查脚本；后续用隔离 kind/minikube 集群做服务访问、rollout 和清理验证，插件章节分开验证 |
| 低 | 按角色标注内容深度 | 给章节标“第一次必学 / 原理深入 / 生产运维 / 扩展选读”，避免小白把 etcd 恢复和服务网格当作第一天前置条件 |

新手第一轮建议：完成入门实验，然后读第 8–13、24、28、39 章的基础部分。验收是能独立部署、解释对象关系、区分 Running 与 Ready、从 Events/logs 找根因并清理资源。平台级高可用、升级、CNI 和 Operator 放在有实践基础之后。

## 验证结果与边界

- 修订后的 HTML 仍有 48 个章节入口，保留单文件离线阅读。
- YAML 检查覆盖 134 个正文代码块及 4 个实验资源；1 个未渲染的 Helm 模板明确跳过。
- 成功解析 208 份 YAML 文档，其中 103 个内置资源使用 v1.34.0 OpenAPI 检查字段、类型与必填项；38 个插件/组件配置只做 YAML 语法检查，67 个片段不作为完整 API 对象验证。不是 208 个可直接部署的资源。
- 没有重复 YAML 键；修复无效 Cilium 示例与多种配置在同一文档中的键覆盖。
- 对可独立识别、不含终端输出/占位符的 shell 示例作语法检查。命令不会因此自动获得运行环境、权限或正确的业务前提。
- 浏览器检查：所有目录锚点可定位；正文关键词 `memory.low` 可找到第 2 章；清空后恢复 48 个入口；没有重复 DOM ID、外部脚本/样式/图片加载或浏览器控制台错误。页面与 Go 代码转义显示正常。
- 另外检查 19 份完整工作负载清单的 selector 与模板标签，以及卷声明与挂载引用，一致。
- 桌面及窄屏页面无整体横向溢出，窄屏目录打开、遮罩关闭与滚动解锁正常；修复两处 SVG 文本越界。
- `git diff --check` 通过。

**未验证范围：**真实集群部署和故障恢复、云存储/云负载均衡、CRD 的插件 schema 与准入逻辑、Helm 渲染、Go Operator 编译、全部镜像拉取及多架构运行。etcd 恢复、集群升级与安全治理示例须在隔离环境按具体版本演练。网站尚未发布本次本地订正。

可复现静态检查（Python 需安装 PyYAML，不连接任何集群）：

```bash
python3 scripts/validate_content.py
```

加入官方 OpenAPI 字段检查：

```bash
curl -fL https://raw.githubusercontent.com/kubernetes/kubernetes/v1.34.0/api/openapi-spec/swagger.json -o /tmp/learnk8s-openapi-v1.34.json
python3 scripts/validate_content.py --schema /tmp/learnk8s-openapi-v1.34.json
```

此脚本检查语法、重复字段、基础字段类型与必填项，不替代 apiserver 对字段值、跨字段约束、准入策略和运行时前置条件的完整校验。

## 2026-10-02 补充：Apple container 实验路线

- 正文 43 章全部增加可展开的实验卡，包含任务、可复制命令、验收与环境前提；附录 E 完整收录 Apple 指南与 43 章索引。现在共有 49 个章节入口（导论、43 章、5 附录）。
- 新增 [Apple 实验指南](./APPLE_CONTAINER_GUIDE.md)，按 E00–E10 组织：环境、隔离、构建、生命周期、网络/DNS、卷、权限/资源、日志、Kubernetes 镜像流转、深入前提、清理。
- 核对 [1.0.0 发布源码](https://github.com/apple/container/tree/1.0.0)、[命令说明](https://github.com/apple/container/blob/1.0.0/docs/command-reference.md)、[技术说明](https://github.com/apple/container/blob/1.0.0/docs/technical-overview.md) 与 [官方入门](https://github.com/apple/container/blob/1.0.0/docs/tutorials/start-here.md)。本机 macOS 27.0.1 / arm64 / container 1.0.0 已运行原生实验。
- 订正实际 IP 提取路径为 `status.networks[].ipv4Address`；官方 how-to 中旧示例的顶层 `networks[].address` 与本机 1.0.0 输出不同。检查版本与实际数据，避免照抄旧字段。
- Kubernetes 衔接使用独立 minikube QEMU/containerd 节点与镜像归档；依据 [QEMU 驱动说明](https://minikube.sigs.k8s.io/docs/drivers/qemu/)、[镜像加载命令](https://minikube.sigs.k8s.io/docs/commands/image/) 和 [Kubernetes 镜像规则](https://kubernetes.io/docs/concepts/containers/images/)。明确 Apple 1.0.0 不能作为 docker 驱动或 CRI endpoint。主分支实验性的 container k8s 不作为已发布 1.0.0 的能力。
- 配套 Dockerfile 与 7 份完整 Kubernetes 清单（12 个资源对象）：网站、ConfigMap、NetworkPolicy、PVC/写入 Pod、RBAC、HPA、ResourceQuota；插件和权限条件分别标注，按章独立部署。
- 由 `scripts/sync_apple_labs.py` 将指南及 JSON 任务同步到离线 HTML；`--check` 核查一致性，避免 43 章、Markdown 与网页长期漂移。
- 本轮 YAML/OpenAPI 检查：220 份 YAML 文档、115 个内置资源字段检查；38 个组件/自定义配置与 67 个片段仍只做语法检查，1 个未渲染 Helm 模板跳过。

**实测与限制：**Apple 网站构建/访问、非 root、停止/启动、专用网络通信及跨网络隔离、DNS、只读目录挂载、命名卷持久化、只读根/capability/环境变量、stats/logs、镜像 save/load 通过。新增 Kubernetes 清单只做静态检查；本机缺少 QEMU，也没有可用的原 Docker 驱动，因此没有启动 Kubernetes 集群，未实际验收节点镜像导入、Pod、插件、多节点或 HA。所有短时验证资源使用 lk8s-ac 前缀，并在验证后清理。

本轮网页核查：49 个目录入口和 43 个实验卡/索引均完整，内部锚点及本地文件链接有效；搜索 Apple container 返回 45 个相关入口，清空后恢复 49 个。实验索引深链接会自动展开卡片；桌面与 500px 窄屏无整体横向溢出，窄屏导航正常开合且释放滚动锁，未见控制台错误或外部资源加载。59 组新增命令通过 bash/zsh 语法检查；语法检查不代替集群执行。

## 2026-10-02 补充：页面与手机 / 平板阅读优化

首屏重写为三个学习入口：小白入门、Apple container、原理学习；缩短导论说明，明确完整清单与配置片段的区别。正文最大行宽约 920px，提升辅助文字和代码注释的对比度。实验卡折叠时显示任务，展开后按准备环境、命令、观察结果和适用范围组织；附录 E 增加步骤导航与纯命令复制。

手机与平板增加固定阅读导航、当前章节、语义化目录按钮、关闭按钮、44px 触控区域及大字号搜索。目录开合同步焦点、背景滚动、aria-expanded 和隐藏目录的不可交互状态，支持 Escape 关闭、Tab 循环及章节跳转后定位标题。平板入口为双列，手机为单列；代码保持格式，宽表格、代码和图示只在自身区域横向滚动，并按实际溢出显示提示。修复两处网格卡片最小宽度导致的手机页面横向溢出；为 SVG 保留可读宽度，支持系统减少动态效果偏好。

验证使用浏览器视口/触控模拟，宽度覆盖 320、390、768、1024、1180、1440、1920px，包括手机、平板纵横屏和电脑宽屏；均未出现页面整体横向溢出。检查 49 个章节入口、43 个实验卡、内部锚点、搜索/空结果/清空、目录遮罩和滚动解锁、Tab/Escape、实验卡 Enter 展开、宽表格键盘滚动、深链接展开、当前章节提示及无外部资源加载。复制检查使用隔离页面的剪贴板替身，确认复制文本与代码一致，并验证受限时的代码选择回退；没有覆盖用户剪贴板。

静态核查仍覆盖 220 份 YAML 文档及 115 个内置资源；所有实验数据与离线 HTML 同步。此轮只调整呈现与阅读操作，Kubernetes 运行验证边界见上节。视口模拟不等同于所有真实设备与浏览器组合的兼容性验收。
