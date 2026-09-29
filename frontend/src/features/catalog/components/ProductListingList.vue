<template>
  <q-list bordered separator>
    <q-item v-for="listing in listings" :key="listing.product.id">
      <q-item-section avatar>
        <span class="text-h5">{{ productEmoji(listing.product.name) }}</span>
      </q-item-section>
      <q-item-section>
        <q-item-label>{{ listing.product.name }}</q-item-label>
        <q-item-label caption>
          <template v-if="listing.ingredient !== null"
            >Składnik: {{ listing.ingredient.name }}</template
          >
          <template v-else>Bez składnika</template>
          <template v-if="listing.product.package !== null">
            · opakowanie {{ formatQuantity(listing.product.package.quantity) }}
            {{ findUnitName(listing.product.package.unitCode) }}
          </template>
        </q-item-label>
      </q-item-section>
      <q-item-section side>
        <div class="row no-wrap items-center q-gutter-xs">
          <q-badge
            v-if="listing.openProposalCount > 0"
            color="orange"
            :label="`Propozycje: ${listing.openProposalCount}`"
          />
          <q-btn
            flat
            dense
            round
            icon="edit"
            aria-label="Edytuj"
            @click="emit('edit', listing.product)"
          />
          <q-btn
            flat
            dense
            round
            color="negative"
            icon="delete"
            :aria-label="`Usuń ${listing.product.name}`"
            @click="emit('remove', listing.product)"
          />
        </div>
      </q-item-section>
    </q-item>
    <q-item v-if="listings.length === 0">
      <q-item-section class="text-grey">Brak produktów.</q-item-section>
    </q-item>
  </q-list>
</template>

<script setup lang="ts">
import { formatQuantity } from '@/shared/formatQuantity';
import { productEmoji } from '@/shared/productEmoji';
import type { Product, ProductListing } from '../model';

defineProps<{ listings: ProductListing[]; findUnitName: (code: string) => string }>();

const emit = defineEmits<{ edit: [product: Product]; remove: [product: Product] }>();
</script>
