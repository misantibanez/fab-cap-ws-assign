import msal
import requests

CLIENT_ID = "service_principal_client_id_value"
TENANT_ID = "tenant_id"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"

BASE_URL = "https://api.fabric.microsoft.com/v1/"
WORKSPACES_URL = "https://api.fabric.microsoft.com/v1/workspaces"
CAPACITY_ID = "capacity_id_value"

SCOPES = [
    "https://api.fabric.microsoft.com/Workspace.ReadWrite.All",
    "https://api.fabric.microsoft.com/Capacity.ReadWrite.All"
]

app = msal.PublicClientApplication(client_id=CLIENT_ID, authority=AUTHORITY)

flow = app.initiate_device_flow(scopes=SCOPES)

if "user_code" not in flow:
    raise Exception("No se pudo iniciar el Device Code Flow")

print(" Ve a la URL y escribe este código para autenticarte:")
print(flow["message"])  # contiene la URL y el código

result = app.acquire_token_by_device_flow(flow)

if "access_token" in result:
    access_token = result["access_token"]
    print(" Token obtenido correctamente")
else:
    print(" Error obteniendo token:")
    print(result.get("error_description"))
    exit(1)


headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

def get_workspaces():
    response = requests.get(WORKSPACES_URL, headers=headers)
    if response.status_code == 200:
        return response.json().get("value", [])
    else:
        print(f"Error {response.status_code}: {response.text}")
        return []


def assign_capacity_to_workspace(workspace_id: str, workspace_name: str) -> bool:
    url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/assignToCapacity"
    body = {"capacityId": CAPACITY_ID}
    response = requests.post(url, headers=headers, json=body)
    try:
        payload = response.json()
    except ValueError:
        payload = None
    if response.status_code in (200, 202):
        print(f" Workspace '{workspace_name}' ({workspace_id}) asignado a capacity {CAPACITY_ID}")
        return True
    if response.status_code == 400:
        msg = ""
        if isinstance(payload, dict):
            msg = payload.get("message") or payload.get("error_description") or payload
        else:
            msg = response.text
        print(f" Error 400 asignando '{workspace_name}': {msg}")
        return False
    print(f" Error {response.status_code} asignando '{workspace_name}': {response.text}")
    return False


if __name__ == "__main__":
    workspaces = get_workspaces()
    total_workspaces = len(workspaces)
    assigned_count = 0
    failed_count = 0
    if workspaces:
        print(f"\n Se encontraron {total_workspaces} workspaces.\n")
        for ws in workspaces:
            success = assign_capacity_to_workspace(ws["id"], ws["displayName"])
            if success:
                assigned_count += 1
            else:
                failed_count += 1
        print("\n Resumen:")
        print(f"   - Total de workspaces encontrados: {total_workspaces}")
        print(f"   - Workspaces asignados correctamente: {assigned_count}")
        print(f"   - Workspaces con error: {failed_count}")
