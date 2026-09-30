<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="text-h5 col">Dom</div>
      <q-btn color="primary" icon="add" label="Nowy dom" no-caps @click="createHousehold" />
    </div>

    <q-banner v-if="households.isLoaded && !households.hasHousehold" class="bg-grey-3 q-mb-md">
      Nie należysz jeszcze do żadnego gospodarstwa domowego. Utwórz pierwsze, aby korzystać z
      zapasów, przepisów i list zakupów.
    </q-banner>

    <HouseholdList
      :households="households.households"
      :selected-id="households.selectedId"
      @select="households.select"
      @rename="renameHousehold"
      @remove="removeHousehold"
    />

    <template v-if="households.selected !== null">
      <div class="text-h6 q-mt-lg q-mb-sm">Osoby w domu: {{ households.selected.name }}</div>
      <HouseholdMembers
        :members="memberList"
        :busy="isMemberBusy"
        :add-member="addMember"
        @remove="removeMember"
      />
    </template>

    <q-expansion-item
      class="q-mt-lg"
      icon="restore_from_trash"
      label="Usunięte domy"
      @show="loadDeleted"
    >
      <div v-if="deletedHouseholds.length === 0" class="q-pa-md text-grey-7">
        Brak usuniętych domów
      </div>
      <DeletedHouseholdList v-else :households="deletedHouseholds" @restore="restoreHousehold" />
    </q-expansion-item>
  </q-page>
</template>

<script setup lang="ts">
import { toRef } from 'vue';
import DeletedHouseholdList from '@/features/households/components/DeletedHouseholdList.vue';
import HouseholdList from '@/features/households/components/HouseholdList.vue';
import HouseholdMembers from '@/features/households/components/HouseholdMembers.vue';
import { HOUSEHOLD_ERROR_MESSAGES } from '@/features/households/errors';
import type { Household, HouseholdMember } from '@/features/households/model';
import { useHouseholdStore } from '@/features/households/store';
import { useDeletedHouseholds } from '@/features/households/useDeletedHouseholds';
import { useHouseholdMembers } from '@/features/households/useHouseholdMembers';
import { useApiAction } from '@/shared/useApiAction';
import { useDialogs } from '@/shared/useDialogs';

const households = useHouseholdStore();
const selectedId = toRef(households, 'selectedId');
const {
  members: memberList,
  busy: isMemberBusy,
  add: addHouseholdMember,
  remove: removeHouseholdMember,
} = useHouseholdMembers(selectedId);
const {
  deleted: deletedHouseholds,
  load: loadDeleted,
  restore: restoreHousehold,
} = useDeletedHouseholds();
const dialogs = useDialogs();
const { run } = useApiAction(HOUSEHOLD_ERROR_MESSAGES);

async function createHousehold(): Promise<void> {
  const name = await dialogs.promptText({ title: 'Nowy dom', label: 'Nazwa', initial: '' });
  if (name === null) {
    return;
  }
  const isCreated = await run(() => households.create(name));
  if (isCreated) {
    dialogs.notifySuccess('Utworzono gospodarstwo domowe.');
  }
}

async function renameHousehold(household: Household): Promise<void> {
  const prompt = { title: 'Zmień nazwę domu', label: 'Nazwa', initial: household.name };
  const name = await dialogs.promptText(prompt);
  if (name === null) {
    return;
  }
  await run(() => households.rename(household.id, name));
}

async function removeHousehold(household: Household): Promise<void> {
  const message = `Dom „${household.name}” zniknie dla wszystkich osób. Można go przywrócić przez pewien czas.`;
  const isConfirmed = await dialogs.confirm('Usunąć dom?', message);
  if (!isConfirmed) {
    return;
  }
  await run(() => households.remove(household.id));
}

async function addMember(username: string): Promise<boolean> {
  const householdId = households.selectedId;
  if (householdId === null) {
    return false;
  }
  const isAdded = await addHouseholdMember(householdId, username);
  households.refreshMemberCount(householdId, memberList.value.length);
  return isAdded;
}

async function removeMember(member: HouseholdMember): Promise<void> {
  const householdId = households.selectedId;
  if (householdId === null) {
    return;
  }
  const message = `Czy usunąć użytkownika ${member.username} z gospodarstwa domowego?`;
  const isConfirmed = await dialogs.confirm('Usunąć osobę?', message);
  if (!isConfirmed) {
    return;
  }
  await removeHouseholdMember(householdId, member);
  households.refreshMemberCount(householdId, memberList.value.length);
}
</script>
