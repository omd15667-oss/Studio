// simple api client used by the frontend - can be expanded later
export async function api(path, opts = {}) {
  const res = await fetch(path, opts)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}
