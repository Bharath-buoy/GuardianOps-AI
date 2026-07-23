"""LangGraph multi-agent workflow endpoints."""
from fastapi import APIRouter

from app.agents.graph import AGENT_SEQUENCE, execute_workflow
from app.models.workflow import WorkflowRunRequest
from app.services.mock_data import store

router = APIRouter(prefix="/workflow", tags=["Workflow"])


@router.get("/nodes")
async def get_workflow_nodes():
    """Static node/edge definition used to render the React Flow diagram."""
    node_ids = [a[0] for a in AGENT_SEQUENCE] + ["mongodb", "dashboard-update"]
    nodes = [{"id": aid, "label": name, "type": "agent"} for aid, name in AGENT_SEQUENCE]
    nodes.append({"id": "mongodb", "label": "MongoDB", "type": "storage"})
    nodes.append({"id": "dashboard-update", "label": "Dashboard Update", "type": "output"})

    edges = []
    for i in range(len(AGENT_SEQUENCE) - 1):
        edges.append({"source": AGENT_SEQUENCE[i][0], "target": AGENT_SEQUENCE[i + 1][0]})
    edges.append({"source": AGENT_SEQUENCE[-1][0], "target": "mongodb"})
    edges.append({"source": "mongodb", "target": "dashboard-update"})

    return {"nodes": nodes, "edges": edges}


@router.post("/run")
async def run_workflow(payload: WorkflowRunRequest = WorkflowRunRequest()):
    run = await execute_workflow(trigger=payload.trigger, target_service_id=payload.target_service_id)
    store.add_workflow_run(run)
    return run


@router.get("/history")
async def get_workflow_history(limit: int = 20):
    runs = store.get_workflow_runs(limit=limit)
    return {"total": len(store.workflow_runs), "runs": runs}
