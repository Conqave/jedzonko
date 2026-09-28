<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="text-h5 col">Dom</div>
      <q-btn color="primary" icon="add" label="Nowy dom" no-caps @click="openCreate" />
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
          <div class="row items-center no-wrap q-gutter-xs">
            <q-icon
              v-if="household.id === households.selectedId"
              name="check_circle"
              color="primary"
            />
            <q-btn flat dense round icon="more_vert" aria-label="Opcje domu" @click.stop>
              <q-menu>
                <q-list style="min-width: 180px">
                  <q-item clickable v-close-popup @click="openRename(household)">
                    <q-item-section avatar><q-icon name="edit" /></q-item-section>
                    <q-item-section>Zmień nazwę</q-item-section>
                  </q-item>
                </q-list>
              </q-menu>
            </q-btn>
          </div>
        </q-item-section>
      </q-item>
    </q-list>

    <template v-if="households.selected !== null">
      <div class="text-h6 q-mt-lg q-mb-sm">Osoby w domu — {{ households.selected.name }}</div>

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
            label="Dodaj osobę"
            no-caps
            :loading="addingMember"
          />
        </div>
      </q-form>

      <q-list bordered separator>
        <q-item v-for="member in members" :key="member.user_id">
          <q-item-section>{{ member.username }}</q-item-section>
          <q-item-section side>
            <q-btn flat dense round icon="more_vert" :aria-label="`Opcje ${member.username}`">
              <q-menu>
                <q-list>
                  <q-item
                    clickable
                    v-close-popup
                    class="text-negative"
                    @click="confirmRemoveMember(member)"
                  >
                    <q-item-section avatar
                      ><q-icon name="delete" color="negative"
                    /></q-item-section>
                    <q-item-section>Usuń z domu</q-item-section>
                  </q-item>
                </q-list>
              </q-menu>
            </q-btn>
          </q-item-section>
        </q-item>
      </q-list>
    </template>

    <q-dialog v-model="createDialogOpen">
      <q-card style="min-width: 320px">
        <q-card-section class="text-h6">Nowy dom</q-card-section>
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

    <q-dialog v-model="renameOpen">
      <q-card style="min-width: 320px">
        <q-card-section class="text-h6">Zmień nazwę gospodarstwa</q-card-section>
        <q-form @submit.prevent="submitRename">
          <q-card-section>
            <q-input
              v-model="renameName"
              autofocus
              dense
              outlined
              label="Nazwa"
              :rules="[(value) => !!value || 'Podaj nazwę']"
            />
          </q-card-section>
          <q-card-actions align="right">
            <q-btn v-close-popup flat label="Anuluj" no-caps />
            <q-btn type="submit" color="primary" label="Zapisz" no-caps :loading="renaming" />
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
import type { Household, HouseholdMember } from '@/features/households/models';
import { useHouseholdStore } from '@/features/households/store';

const quasar = useQuasar();
const households = useHouseholdStore();

const members = ref<HouseholdMember[]>([]);
const renameOpen = ref(false);
const renameName = ref('');
const renameId = ref<number | null>(null);
const renaming = ref(false);

function openRename(household: Household): void {
  renameId.value = household.id;
  renameName.value = household.name;
  renameOpen.value = true;
}

async function submitRename(): Promise<void> {
  if (renameId.value === null) {
    return;
  }
  renaming.value = true;
  try {
    await households.rename(renameId.value, renameName.value.trim());
    renameOpen.value = false;
  } catch (error) {
    quasar.notify({ type: 'negative', message: describeHouseholdError(error) });
  } finally {
    renaming.value = false;
  }
}
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
