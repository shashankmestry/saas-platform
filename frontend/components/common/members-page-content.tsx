"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";

import { useOrganization } from "@/components/providers/organization-provider";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  OrganizationPermission,
  OrganizationRole,
} from "@/lib/auth/permissions";
import {
  inviteMemberSchema,
  type InviteMemberFormValues,
} from "@/lib/organizations/invite-schema";
import { membershipKeys, organizationKeys } from "@/lib/query-keys";
import {
  createOrganizationInvitation,
  listOrganizationInvitations,
  listOrganizationMembers,
  removeMember,
  revokeOrganizationInvitation,
  transferOwnership,
  updateMemberRole,
} from "@/services/memberships";
import { useAuthStore } from "@/store/auth";
import type { OrganizationMember } from "@/types";

function formatExpiry(value: string): string {
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

export function MembersPageContent() {
  const queryClient = useQueryClient();
  const currentUser = useAuthStore((state) => state.user);
  const { organization, can, invalidateOrganizationQueries } = useOrganization();
  const [error, setError] = useState<string | null>(null);
  const [inviteNotice, setInviteNotice] = useState<string | null>(null);
  const [transferTargetId, setTransferTargetId] = useState("");

  const canViewMembers = can(OrganizationPermission.MEMBER_VIEW);
  const canViewInvitations = can(OrganizationPermission.INVITATION_VIEW);
  const canInvite = can(OrganizationPermission.MEMBER_INVITE);
  const canRevoke = can(OrganizationPermission.INVITATION_REVOKE);
  const canUpdateRole = can(OrganizationPermission.MEMBER_ROLE_UPDATE);
  const canRemove = can(OrganizationPermission.MEMBER_REMOVE);
  const canTransfer = can(OrganizationPermission.ORGANIZATION_OWNERSHIP_TRANSFER);

  const membersQuery = useQuery({
    queryKey: membershipKeys.members(organization?.id ?? ""),
    queryFn: () => listOrganizationMembers(organization!.id),
    enabled: Boolean(organization?.id) && canViewMembers,
  });

  const invitationsQuery = useQuery({
    queryKey: membershipKeys.invitations(organization?.id ?? ""),
    queryFn: () => listOrganizationInvitations(organization!.id),
    enabled: Boolean(organization?.id) && canViewInvitations,
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<InviteMemberFormValues>({
    resolver: zodResolver(inviteMemberSchema),
    defaultValues: {
      email: "",
    },
  });

  async function invalidateMembershipData() {
    if (!organization) {
      return;
    }
    await Promise.all([
      queryClient.invalidateQueries({
        queryKey: membershipKeys.members(organization.id),
      }),
      queryClient.invalidateQueries({
        queryKey: membershipKeys.invitations(organization.id),
      }),
      queryClient.invalidateQueries({
        queryKey: organizationKeys.plan(organization.id),
      }),
      queryClient.invalidateQueries({ queryKey: organizationKeys.list() }),
    ]);
  }

  const inviteMutation = useMutation({
    mutationFn: (email: string) =>
      createOrganizationInvitation(organization!.id, email),
    onSuccess: async (invitation) => {
      reset();
      setError(null);
      await invalidateMembershipData();
      setInviteNotice(
        invitation.invite_url
          ? `Invitation created. Development invite URL: ${invitation.invite_url}`
          : "Invitation created.",
      );
    },
    onError: (inviteError: Error) => {
      setError(inviteError.message);
    },
  });

  const revokeMutation = useMutation({
    mutationFn: (invitationId: string) =>
      revokeOrganizationInvitation(organization!.id, invitationId),
    onSuccess: async () => {
      setError(null);
      await invalidateMembershipData();
    },
    onError: (revokeError: Error) => {
      setError(revokeError.message);
    },
  });

  const roleMutation = useMutation({
    mutationFn: ({
      membershipId,
      role,
    }: {
      membershipId: string;
      role: "owner" | "member";
    }) => updateMemberRole(organization!.id, membershipId, role),
    onSuccess: async () => {
      setError(null);
      await invalidateMembershipData();
      await invalidateOrganizationQueries();
    },
    onError: (roleError: Error) => {
      setError(roleError.message);
    },
  });

  const removeMutation = useMutation({
    mutationFn: (membershipId: string) =>
      removeMember(organization!.id, membershipId),
    onSuccess: async () => {
      setError(null);
      await invalidateMembershipData();
    },
    onError: (removeError: Error) => {
      setError(removeError.message);
    },
  });

  const transferMutation = useMutation({
    mutationFn: (membershipId: string) =>
      transferOwnership(organization!.id, membershipId),
    onSuccess: async () => {
      setError(null);
      setTransferTargetId("");
      await invalidateMembershipData();
      await invalidateOrganizationQueries();
    },
    onError: (transferError: Error) => {
      setError(transferError.message);
    },
  });

  const transferCandidates = useMemo(() => {
    const members = membersQuery.data ?? [];
    return members.filter((member) => member.user_id !== currentUser?.id);
  }, [currentUser?.id, membersQuery.data]);

  if (!organization) {
    return null;
  }

  const isLoading =
    (canViewMembers && membersQuery.isLoading) ||
    (canViewInvitations && invitationsQuery.isLoading);

  if (isLoading) {
    return (
      <main className="flex flex-1 items-center justify-center px-6 py-16">
        <p className="text-muted-foreground text-sm">Loading members...</p>
      </main>
    );
  }

  function confirmAndUpdateRole(member: OrganizationMember, role: "owner" | "member") {
    const label = role === "owner" ? "owner" : "member";
    const confirmed = window.confirm(`Change ${member.email} to ${label}?`);
    if (!confirmed) {
      return;
    }
    roleMutation.mutate({ membershipId: member.id, role });
  }

  function confirmAndRemove(member: OrganizationMember) {
    const confirmed = window.confirm(
      `Remove ${member.email} from ${organization?.name ?? "this organization"}?`,
    );
    if (!confirmed) {
      return;
    }
    removeMutation.mutate(member.id);
  }

  function confirmAndTransfer() {
    if (!transferTargetId) {
      return;
    }
    const target = transferCandidates.find((member) => member.id === transferTargetId);
    const confirmed = window.confirm(
      `Transfer ownership to ${target?.email ?? "this member"}? You will become a member.`,
    );
    if (!confirmed) {
      return;
    }
    transferMutation.mutate(transferTargetId);
  }

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-6 py-12">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Members</h1>
        <p className="text-muted-foreground text-sm">{organization.name}</p>
      </div>

      {error ? (
        <p className="text-destructive text-sm" role="alert">
          {error}
        </p>
      ) : null}

      {inviteNotice ? (
        <p className="text-muted-foreground text-sm break-all" role="status">
          {inviteNotice}
        </p>
      ) : null}

      {canViewMembers ? (
        <Card>
          <CardHeader>
            <CardTitle>Members</CardTitle>
            <CardDescription>People who belong to this organization.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {(membersQuery.data?.length ?? 0) === 0 ? (
              <p className="text-muted-foreground text-sm">No members found.</p>
            ) : (
              (membersQuery.data ?? []).map((member) => (
                <div
                  key={member.id}
                  className="flex flex-col gap-2 border-b border-border py-3 last:border-0 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div>
                    <p className="font-medium">{member.display_name ?? member.email}</p>
                    <p className="text-muted-foreground text-sm">{member.email}</p>
                    <p className="text-muted-foreground text-xs capitalize">{member.role}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {canUpdateRole && member.role !== OrganizationRole.OWNER ? (
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => confirmAndUpdateRole(member, "owner")}
                        disabled={roleMutation.isPending}
                      >
                        Make owner
                      </Button>
                    ) : null}
                    {canUpdateRole && member.role === OrganizationRole.OWNER ? (
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => confirmAndUpdateRole(member, "member")}
                        disabled={roleMutation.isPending}
                      >
                        Make member
                      </Button>
                    ) : null}
                    {canRemove && member.user_id !== currentUser?.id ? (
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => confirmAndRemove(member)}
                        disabled={removeMutation.isPending}
                      >
                        Remove
                      </Button>
                    ) : null}
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      ) : null}

      {canInvite ? (
        <Card>
          <CardHeader>
            <CardTitle>Invite member</CardTitle>
            <CardDescription>Send an invitation by email.</CardDescription>
          </CardHeader>
          <CardContent>
            <form
              className="flex flex-col gap-3 sm:flex-row sm:items-end"
              onSubmit={handleSubmit((values) => inviteMutation.mutate(values.email))}
              noValidate
            >
              <div className="flex-1 space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" {...register("email")} />
                {errors.email ? (
                  <p className="text-destructive text-sm">{errors.email.message}</p>
                ) : null}
              </div>
              <Button type="submit" disabled={isSubmitting || inviteMutation.isPending}>
                {inviteMutation.isPending ? "Inviting..." : "Invite"}
              </Button>
            </form>
          </CardContent>
        </Card>
      ) : null}

      {canViewInvitations ? (
        <Card>
          <CardHeader>
            <CardTitle>Pending invitations</CardTitle>
            <CardDescription>Invitations that have not been accepted yet.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {(invitationsQuery.data?.length ?? 0) === 0 ? (
              <p className="text-muted-foreground text-sm">No pending invitations.</p>
            ) : (
              (invitationsQuery.data ?? []).map((invitation) => (
                <div
                  key={invitation.id}
                  className="flex flex-col gap-2 border-b border-border py-3 last:border-0 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div>
                    <p className="font-medium">{invitation.email}</p>
                    <p className="text-muted-foreground text-xs">
                      Expires {formatExpiry(invitation.expires_at)}
                    </p>
                  </div>
                  {canRevoke ? (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => revokeMutation.mutate(invitation.id)}
                      disabled={revokeMutation.isPending}
                    >
                      Revoke
                    </Button>
                  ) : null}
                </div>
              ))
            )}
          </CardContent>
        </Card>
      ) : null}

      {canTransfer ? (
        <Card>
          <CardHeader>
            <CardTitle>Transfer ownership</CardTitle>
            <CardDescription>
              Choose another member to become the organization owner.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3 sm:flex-row sm:items-end">
            <div className="flex-1 space-y-2">
              <Label htmlFor="transferTarget">New owner</Label>
              <select
                id="transferTarget"
                className="border-input h-8 w-full rounded-lg border bg-transparent px-2.5 text-sm"
                value={transferTargetId}
                onChange={(event) => setTransferTargetId(event.target.value)}
              >
                <option value="">Select member</option>
                {transferCandidates.map((member) => (
                  <option key={member.id} value={member.id}>
                    {member.email}
                  </option>
                ))}
              </select>
            </div>
            <Button
              type="button"
              variant="outline"
              disabled={!transferTargetId || transferMutation.isPending}
              onClick={confirmAndTransfer}
            >
              {transferMutation.isPending ? "Transferring..." : "Transfer"}
            </Button>
          </CardContent>
        </Card>
      ) : null}
    </main>
  );
}
