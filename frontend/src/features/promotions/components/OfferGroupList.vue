<template>
  <q-list bordered separator>
    <template v-for="group in groups" :key="group.shopSlug">
      <q-item-label header>{{ group.shopName }}</q-item-label>
      <q-item v-for="(offer, index) in group.offers" :key="`${group.shopSlug}-${index}`">
        <q-item-section avatar>
          <q-avatar rounded>
            <img :src="offer.imageUrl" :alt="offer.name" />
          </q-avatar>
        </q-item-section>
        <q-item-section>
          <q-item-label>{{ offer.name }}</q-item-label>
          <q-item-label caption>
            <span v-if="offer.brandName !== null">{{ offer.brandName }} · </span>
            do {{ offer.validUntil }}
          </q-item-label>
        </q-item-section>
        <q-item-section side>
          <q-item-label class="text-weight-bold">{{ formatPrice(offer.price) }}</q-item-label>
          <q-btn
            flat
            dense
            no-caps
            size="sm"
            label="Gazetka"
            type="a"
            :href="offer.leafletUrl"
            target="_blank"
          />
        </q-item-section>
      </q-item>
    </template>
  </q-list>
</template>

<script setup lang="ts">
import { formatPrice, type OfferGroup } from '../model';

defineProps<{ groups: OfferGroup[] }>();
</script>
