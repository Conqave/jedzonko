<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="text-h5 col">Gospodarstwa domowe</div>
      <q-btn color="primary" icon="add" label="Nowe gospodarstwo" no-caps @click="openCreate" />
    </div>

    <q-banner v-if="households.loaded && !households.hasHousehold" class="bg-grey-3 q-mb-md">
      Nie należysz jeszcze do żadnego gospodarstwa domowego. Utwórz pierwsze, aby korzystać z
      zapasów, przepisów i list zakupów.
    </q-banner>

    <q-list bordered separator>
      <q-item
        v-for="household in households.households"
        :key="household.id"
        clickable
        :active="household.id === households.selectedId"
        active-class="bg-blue-1"
        @click="selectHousehold(household.id)"
      >
        <q-item-section>
          <q-item-label>{{ household.name }}</q-item-label>
          <q-item-label caption>{{ household.member_count }} członków</q-item-label>
        </q-item-section>
        <q-item-section side>
          <q-icon
            v-if="household.id === households.selectedId"
            name="check_circle"
            color="primary"
          />
        </q-item-section>
      </q-item>
    </q-list>

    <template v-if="households.selected !== null">
      <div class="text-h6 q-mt-lg q-mb-sm">Członkowie — {{ households.selected.name }}</div>

      <q-form class="row q-col-gutter-sm q-mb-md" @submit.prevent="submitMember">
        <div class="col-12 col-sm-6">
          <q-input
            v-model="newMemberUsername"
            dense
            outlined
            label="Nazwa użytkownika"
            :rules="[(value) => !!value || 'Podaj nazwę użytkownika']"
          />
        </div>
        <div class="col-12 col-sm-4">
          <q-btn
            type="submit"
            color="primary"
            label="Dodaj członka"
            no-caps
            :loading="addingMember"
          />
        </div>
      </q-form>

      <q-list bordered separator>
        <q-item v-for="member in members" :key="member.user_id">
          <q-item-section>{{ member.username }}</q-item-section>
          <q-item-section side>
            <q-btn
              flat
              dense
              round
              color="negative"
              icon="delete"
              :aria-label="`Usuń ${member.username}`"
              @click="confirmRemoveMember(member)"
            />
          </q-item-section>
        </q-item>
      </q-list>
    </template>

    <q-dialog v-model="createDialogOpen">
      <q-card style="min-width: 320px">
        <q-card-section class="text-h6">Nowe gospodarstwo domowe</q-card-section>
        <q-form @submit.prevent="submitCreate">
          <q-card-section>
            <q-input
              v-model="newHouseholdName"
              autofocus
              dense
              outlined
              label="Nazwa"
              :rules="[(value) => !!value || 'Podaj nazwę']"
            />
          </q-card-section>
          <q-card-actions align="right">
            <q-btn v-close-popup flat label="Anuluj" no-caps />
            <q-btn type="submit" color="primary" label="Utwórz" no-caps :loading="creating" />
          </q-card-actions>
        </q-form>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import { useQuasar } from 'quasar';
import { addMember, fetchMembers, removeMember } from '@/features/households/api';
import { describeHouseholdError } from '@/features/households/errors';
import type { HouseholdMember } from '@/features/households/models';
import { useHouseholdStore } from '@/features/households/store';

const quasar = useQuasar();
const households = useHouseholdStore();

const members = ref<HouseholdMember[]>([]);
const newMemberUsername = ref('');
const addingMember = ref(false);
const createDialogOpen = ref(false);
const newHouseholdName = ref('');
const creating = ref(false);

function notifyError(error: unknown): void {
  quasar.notify({ type: 'negative', message: describeHouseholdError(error) });
}

async function loadMembers(): Promise<void> {
  if (households.selectedId === null) {
    members.value = [];
    return;
  }
  try {
    members.value = await fetchMembers(households.selectedId);
  } catch (error) {
    members.value = [];
    notifyError(error);
  }
}

function selectHousehold(householdId: number): void {
  households.select(householdId);
}

function openCreate(): void {
  newHouseholdName.value = '';
  createDialogOpen.value = true;
}

async function submitCreate(): Promise<void> {
  creating.value = true;
  try {
    await households.create(newHouseholdName.value.trim());
    createDialogOpen.value = false;
    quasar.notify({ type: 'positive', message: 'Utworzono gospodarstwo domowe.' });
  } catch (error) {
    notifyError(error);
  } finally {
    creating.value = false;
  }
}

async function submitMember(): Promise<void> {
  if (households.selectedId === null || newMemberUsername.value.trim() === '') {
    return;
  }
  addingMember.value = true;
  try {
    const member = await addMember(households.selectedId, newMemberUsername.value.trim());
    members.value = [...members.value, member];
    newMemberUsername.value = '';
  } catch (error) {
    notifyError(error);
  } finally {
    addingMember.value = false;
  }
}

function confirmRemoveMember(member: HouseholdMember): void {
  quasar
    .dialog({
      title: 'Usunąć członka?',
      message: `Czy usunąć użytkownika ${member.username} z gospodarstwa domowego?`,
      cancel: true,
      persistent: true,
    })
    .onOk(() => {
      void doRemoveMember(member);
    });
}

async function doRemoveMember(member: HouseholdMember): Promise<void> {
  if (households.selectedId === null) {
    return;
  }
  try {
    await removeMember(households.selectedId, member.user_id);
    members.value = members.value.filter((entry) => entry.user_id !== member.user_id);
  } catch (error) {
    notifyError(error);
  }
}

onMounted(() => {
  void loadMembers();
});

watch(
  () => households.selectedId,
  () => {
    void loadMembers();
  },
);
</script>
