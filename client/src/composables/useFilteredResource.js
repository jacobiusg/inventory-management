import { ref, watch, onMounted } from 'vue';

// Returns { data, loading, error, reload } for a resource that:
//  - loads once on mount
//  - reloads whenever any reactive source in `deps` changes
export function useFilteredResource(loader, deps = [], initialValue = null) {
  const data = ref(initialValue);
  const loading = ref(false);
  const error = ref(null);
  const reload = async () => {
    loading.value = true;
    error.value = null;
    try { data.value = await loader(); }
    catch (e) { error.value = e; }
    finally { loading.value = false; }
  };
  if (deps.length) watch(deps, reload);
  onMounted(reload);
  return { data, loading, error, reload };
}
