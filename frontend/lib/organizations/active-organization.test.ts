import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { resolveInitialOrganizationSlug } from "./active-organization.ts";
import {
  organizationHomePath,
  organizationSectionPath,
  replaceOrganizationSlugInPath,
} from "./paths.ts";

describe("resolveInitialOrganizationSlug", () => {
  it("returns null when the user has no organizations", () => {
    assert.equal(resolveInitialOrganizationSlug([], null), null);
  });

  it("opens the only organization when the user has one", () => {
    assert.equal(
      resolveInitialOrganizationSlug([{ slug: "acme" }], "other"),
      "acme",
    );
  });

  it("restores the last selected organization when it still exists", () => {
    assert.equal(
      resolveInitialOrganizationSlug(
        [{ slug: "acme" }, { slug: "beta" }],
        "beta",
      ),
      "beta",
    );
  });

  it("falls back to the first organization when stored slug is invalid", () => {
    assert.equal(
      resolveInitialOrganizationSlug(
        [{ slug: "acme" }, { slug: "beta" }],
        "missing",
      ),
      "acme",
    );
  });

  it("falls back to the first organization when nothing is stored", () => {
    assert.equal(
      resolveInitialOrganizationSlug(
        [{ slug: "acme" }, { slug: "beta" }],
        null,
      ),
      "acme",
    );
  });
});

describe("organization paths", () => {
  it("builds section paths from the immutable slug", () => {
    assert.equal(organizationHomePath("acme"), "/organizations/acme/dashboard");
    assert.equal(
      organizationSectionPath("acme", "members"),
      "/organizations/acme/members",
    );
  });

  it("replaces the slug while keeping the current section", () => {
    assert.equal(
      replaceOrganizationSlugInPath(
        "/organizations/acme/settings",
        "acme",
        "beta",
      ),
      "/organizations/beta/settings",
    );
  });
});
