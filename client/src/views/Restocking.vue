<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking</h2>
      <p>Set a budget and review recommended purchases to replenish forecasted demand.</p>
    </div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Available Budget</h3>
      </div>
      <div class="budget-controls">
        <input
          type="range"
          class="budget-slider"
          :min="1000"
          :max="500000"
          :step="1000"
          v-model.number="budgetRef"
        />
        <div class="budget-display">
          <span class="budget-currency">{{ currencySymbol }}</span>
          <span class="budget-amount">{{ budgetRef.toLocaleString() }}</span>
        </div>
        <input
          type="number"
          class="budget-number"
          :min="1000"
          :max="500000"
          :step="1000"
          v-model.number="budgetRef"
        />
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Recommended Items</h3>
        <div class="recommendations-summary">
          <span>Total: <strong>{{ currencySymbol }}{{ totalCost.toLocaleString() }}</strong></span>
          <span>Budget: <strong>{{ currencySymbol }}{{ budgetRef.toLocaleString() }}</strong></span>
          <span>Remaining: <strong>{{ currencySymbol }}{{ remainingBudget.toLocaleString() }}</strong></span>
        </div>
      </div>

      <div v-if="loading" class="loading">Loading recommendations...</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else class="table-container">
        <table class="recommendations-table">
          <thead>
            <tr>
              <th>SKU</th>
              <th>Name</th>
              <th>Category</th>
              <th>On Hand</th>
              <th>Forecast</th>
              <th>Trend</th>
              <th>Recommended Qty</th>
              <th>Unit Cost</th>
              <th>Line Total</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="items.length === 0">
              <td colspan="9" class="empty-state">No recommendations for this budget.</td>
            </tr>
            <tr v-for="item in items" :key="item.sku">
              <td><strong>{{ item.sku }}</strong></td>
              <td>{{ translateProductName(item.name) }}</td>
              <td>{{ item.category }}</td>
              <td>{{ item.on_hand }}</td>
              <td>{{ item.forecasted_demand }}</td>
              <td>
                <span :class="['badge', item.trend]">{{ item.trend }}</span>
              </td>
              <td><strong>{{ item.recommended_quantity }}</strong></td>
              <td>{{ currencySymbol }}{{ item.unit_cost.toLocaleString() }}</td>
              <td><strong>{{ currencySymbol }}{{ item.line_total.toLocaleString() }}</strong></td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="action-bar">
        <label class="supplier-field">
          <span>Supplier:</span>
          <input type="text" v-model="supplierName" placeholder="Supplier name" />
        </label>
        <button
          class="place-order-btn"
          :disabled="items.length === 0 || placing"
          @click="placeOrder"
        >
          {{ placing ? 'Placing...' : 'Place Order' }}
        </button>
      </div>

      <div v-if="placeError" class="error">{{ placeError }}</div>
      <div v-if="lastPlacedOrder" class="success-banner">
        <span>
          Purchase order <strong>#{{ lastPlacedOrder.id }}</strong> placed successfully.
          Expected delivery: {{ lastPlacedOrder.expected_delivery_date }}
          ({{ lastPlacedOrder.lead_time_days }} days).
        </span>
        <router-link to="/orders" class="view-orders-link">View in Orders</router-link>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { currentCurrency, translateProductName } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const budgetRef = ref(50000)
    const items = ref([])
    const totalCost = ref(0)
    const remainingBudget = ref(0)
    const loading = ref(true)
    const error = ref(null)

    const supplierName = ref('Acme Supply')
    const placing = ref(false)
    const placeError = ref(null)
    const lastPlacedOrder = ref(null)

    let debounceTimer = null

    const loadRecommendations = async () => {
      try {
        loading.value = true
        error.value = null
        const data = await api.getRestockingRecommendations(budgetRef.value)
        items.value = data.items || []
        totalCost.value = data.total_cost || 0
        remainingBudget.value = data.remaining_budget || 0
      } catch (err) {
        error.value = 'Failed to load recommendations: ' + err.message
        items.value = []
        totalCost.value = 0
        remainingBudget.value = 0
      } finally {
        loading.value = false
      }
    }

    watch(budgetRef, () => {
      if (debounceTimer) clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        loadRecommendations()
      }, 250)
    })

    const placeOrder = async () => {
      if (items.value.length === 0) return
      try {
        placing.value = true
        placeError.value = null
        lastPlacedOrder.value = null

        const payload = {
          supplier_name: supplierName.value,
          category: items.value[0].category,
          items: items.value.map(i => ({
            sku: i.sku,
            name: i.name,
            quantity: i.recommended_quantity,
            unit_cost: i.unit_cost
          }))
        }

        const created = await api.createPurchaseOrder(payload)
        lastPlacedOrder.value = created
        await loadRecommendations()
      } catch (err) {
        placeError.value = 'Failed to place order: ' + (err.response?.data?.detail || err.message)
      } finally {
        placing.value = false
      }
    }

    onMounted(loadRecommendations)

    return {
      budgetRef,
      items,
      totalCost,
      remainingBudget,
      loading,
      error,
      currencySymbol,
      translateProductName,
      supplierName,
      placing,
      placeError,
      lastPlacedOrder,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-controls {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 0.5rem 0;
}

.budget-slider {
  flex: 1;
  min-width: 200px;
  cursor: pointer;
}

.budget-display {
  display: flex;
  align-items: baseline;
  gap: 0.25rem;
  min-width: 140px;
  justify-content: flex-end;
}

.budget-currency {
  font-size: 1.25rem;
  color: #64748b;
  font-weight: 500;
}

.budget-amount {
  font-size: 1.75rem;
  font-weight: 700;
  color: #0f172a;
}

.budget-number {
  width: 140px;
  padding: 0.5rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.95rem;
}

.recommendations-summary {
  display: flex;
  gap: 1.5rem;
  font-size: 0.875rem;
  color: #475569;
}

.recommendations-table {
  table-layout: auto;
  width: 100%;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #64748b;
  font-style: italic;
}

.action-bar {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 0 0.25rem 0;
  border-top: 1px solid #f1f5f9;
  margin-top: 1rem;
}

.supplier-field {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
  font-size: 0.875rem;
  color: #475569;
}

.supplier-field input {
  flex: 1;
  max-width: 300px;
  padding: 0.5rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.95rem;
}

.place-order-btn {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 0.625rem 1.25rem;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.place-order-btn:hover:not(:disabled) {
  background: #2563eb;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.success-banner {
  margin-top: 1rem;
  padding: 0.875rem 1rem;
  background: #ecfdf5;
  border: 1px solid #10b981;
  border-radius: 8px;
  color: #065f46;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  font-size: 0.9rem;
}

.view-orders-link {
  color: #047857;
  font-weight: 600;
  text-decoration: underline;
  white-space: nowrap;
}

.view-orders-link:hover {
  color: #065f46;
}
</style>
