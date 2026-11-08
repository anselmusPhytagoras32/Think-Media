// FR02–05/08, W02–W04/W06: mobile discovery backed by published, authorized API data.
import { useEffect, useState, type FormEvent } from "react";
import { ArrowRight, MapPin, Search, SlidersHorizontal } from "lucide-react";
import { api, type Account } from "./api";
import { href } from "./navigation";
import { Artwork } from "./artwork";
import { CompanyCover } from "./company-brand";
import { ResourceArtwork } from "./resource-artwork";
import { ThinkIcon } from "./brand";
import { StatusBadge } from "./status";
import type { Listing, Application } from "./marketplace";
type Page<T> = { items: T[]; total: number };
type Resource = {
  id: string;
  title: string;
  summary: string;
  tags: string[];
  has_quiz: boolean;
};
export function StudentHome({ account }: { account: Account }) {
  const [listings, setListings] = useState<Page<Listing> | null>(null);
  const [resources, setResources] = useState<Page<Resource> | null>(null);
  const [applications, setApplications] = useState<Page<Application> | null>(
    null,
  );
  const [busy, setBusy] = useState(true),
    [error, setError] = useState(""),
    [revision, setRevision] = useState(0);
  useEffect(() => {
    let active = true;
    setBusy(true);
    setError("");
    const get = <T,>(path: string, update: (value: Page<T>) => void) =>
      api<Page<T>>(path).then((data) => {
        if (active) update(data);
      });
    Promise.allSettled([
      get<Listing>("/listings?limit=4", setListings),
      get<Resource>("/content?limit=3", setResources),
      get<Application>("/applications/me?limit=4", setApplications),
    ]).then((result) => {
      if (!active) return;
      setBusy(false);
      if (result.some((x) => x.status === "rejected"))
        setError(
          "Some recent activity could not be loaded. Try again, or use the navigation to open your work.",
        );
    });
    return () => {
      active = false;
    };
  }, [revision]);
  function search(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const keyword = String(
      new FormData(e.currentTarget).get("search") || "",
    ).trim();
    window.location.hash = `#/opportunities${keyword ? `?search=${encodeURIComponent(keyword)}` : ""}`;
  }
  const first = account.user.display_name.split(" ")[0];
  return (
    <div className="consumer-home">
      <div className="consumer-columns">
        <div className="consumer-primary">
          <header className="consumer-intro">
            <div>
              <h1>
                Find your next <em>opportunity.</em>
              </h1>
              <p>
                <span>Hello, {first}.</span> Explore OJT and build your skills.
              </p>
            </div>
            <a
              href={href("profile")}
              className="consumer-profile"
              aria-label="Open my profile"
            >
              <span>{first.slice(0, 1)}</span>
              <ThinkIcon name="profile" size={24} />
            </a>
          </header>
          <form className="consumer-search" onSubmit={search}>
            <Search size={20} aria-hidden="true" />
            <label className="sr-only" htmlFor="consumer-query">
              Search opportunities
            </label>
            <input
              id="consumer-query"
              type="search"
              name="search"
              placeholder="Role, title or keyword"
              maxLength={200}
            />
            <button aria-label="Search opportunities" type="submit">
              <ArrowRight size={21} />
            </button>
            <a
              href={href("opportunities")}
              className="consumer-filter"
              aria-label="Browse opportunity filters"
            >
              <SlidersHorizontal size={20} />
            </a>
          </form>
          <section
            className="discovery-section"
            aria-labelledby="discover-title"
          >
            <div className="discovery-section-heading">
              <h2 id="discover-title">What brings you here?</h2>
              <a href={href("suggestions")}>
                For you <ArrowRight size={15} />
              </a>
            </div>
            <div className="discovery-categories">
              <a className="category-ojt" href="#/opportunities?type=ojt">
                <Artwork kind="opportunities" priority />
                <strong>Find OJT</strong>
                <span>Build experience</span>
              </a>
              <a className="category-learning" href={href("learning")}>
                <Artwork kind="learning" priority />
                <strong>Learn a skill</strong>
                <span>Get prepared</span>
              </a>
              <a className="category-tracker" href={href("applications")}>
                <Artwork kind="applications" priority />
                <strong>My applications</strong>
                <span>Follow your progress</span>
              </a>
            </div>
          </section>
          {error && (
            <div className="notice error" role="alert">
              <div>
                {error}
                <button
                  className="text-button"
                  onClick={() => setRevision((n) => n + 1)}
                >
                  Reload activity
                </button>
              </div>
            </div>
          )}
          <section className="discovery-section" aria-labelledby="recent-title">
            <div className="discovery-section-heading">
              <h2 id="recent-title">Recently posted</h2>
              <a href={href("opportunities")}>
                View all <ArrowRight size={15} />
              </a>
            </div>
            {busy ? (
              <p role="status">Finding opportunities…</p>
            ) : listings?.items.length ? (
              <div
                className="opportunity-carousel"
                role="list"
                aria-label="Recent opportunities"
              >
                {listings.items.map((listing) => (
                  <article
                    className="opportunity-card"
                    role="listitem"
                    key={listing.id}
                  >
                    <a
                      className="opportunity-card-link"
                      href={href("opportunities", listing.id)}
                    >
                      <div className="opportunity-cover">
                        <CompanyCover
                          companyId={listing.company_id}
                          companyName={listing.company_name}
                        />
                        <span>
                          {listing.type === "ojt"
                            ? "OJT placement"
                            : "Job opportunity"}
                        </span>
                      </div>
                      <div className="opportunity-card-copy">
                        <p className="consumer-company">
                          {listing.company_name}
                        </p>
                        <h3>{listing.title}</h3>
                        <p className="consumer-location">
                          <MapPin size={14} />
                          {listing.location}
                        </p>
                        <div className="consumer-skills">
                          {listing.skills.slice(0, 2).map((skill) => (
                            <span key={skill}>{skill}</span>
                          ))}
                        </div>
                        <span className="consumer-card-action">
                          View opportunity <ArrowRight size={16} />
                        </span>
                      </div>
                    </a>
                  </article>
                ))}
              </div>
            ) : (
              listings && (
                <div className="discovery-empty">
                  <Artwork kind="opportunities" />
                  <div>
                    <h3>No open opportunities yet</h3>
                    <p>
                      Verified companies’ published listings will appear here.
                    </p>
                    <a href={href("opportunities")}>
                      Browse opportunities <ArrowRight size={15} />
                    </a>
                  </div>
                </div>
              )
            )}
          </section>
          <section className="discovery-section" aria-labelledby="learn-title">
            <div className="discovery-section-heading">
              <h2 id="learn-title">A little preparation helps</h2>
              <a href={href("learning")}>
                View all <ArrowRight size={15} />
              </a>
            </div>
            {busy ? (
              <p role="status">Loading learning resources…</p>
            ) : resources?.items.length ? (
              <div className="learning-discovery">
                {resources.items.map((item) => (
                  <a
                    className="learning-discovery-card"
                    key={item.id}
                    href={href("learning", item.id)}
                  >
                    <div className="learning-discovery-art">
                      <ResourceArtwork title={item.title} tags={item.tags} />
                    </div>
                    <div>
                      <span>
                        {item.has_quiz
                          ? "Read + try a quiz"
                          : "Learning resource"}
                      </span>
                      <h3>{item.title}</h3>
                      <p>{item.summary}</p>
                      <strong>
                        Read resource <ArrowRight size={15} />
                      </strong>
                    </div>
                  </a>
                ))}
              </div>
            ) : (
              resources && (
                <div className="discovery-empty">
                  <Artwork kind="learning" />
                  <div>
                    <h3>Learning is on its way</h3>
                    <p>
                      Published lessons and preparation tips will appear here.
                    </p>
                    <a href={href("learning")}>
                      Open learning <ArrowRight size={15} />
                    </a>
                  </div>
                </div>
              )
            )}
          </section>
        </div>
        <aside className="consumer-support">
          <section
            className="application-pocket"
            aria-labelledby="application-pocket-title"
          >
            <div className="discovery-section-heading">
              <h2 id="application-pocket-title">Your applications</h2>
              <a href={href("applications")}>
                View all <ArrowRight size={15} />
              </a>
            </div>
            {busy ? (
              <p role="status">Loading applications…</p>
            ) : applications?.items.length ? (
              <div>
                {applications.items.slice(0, 3).map((a) => (
                  <a
                    className="activity-row"
                    key={a.id}
                    href={href("applications", a.id)}
                  >
                    <div>
                      <strong>{a.listing_title}</strong>
                      <span>{a.company_name}</span>
                    </div>
                    <StatusBadge status={a.status} />
                  </a>
                ))}
              </div>
            ) : (
              applications && (
                <>
                  <Artwork kind="applications" />
                  <h3>No applications yet</h3>
                  <p>
                    Find a listing you like, check its requirements and send
                    your PDF when you’re ready.
                  </p>
                  <a className="secondary" href={href("opportunities")}>
                    Find opportunities <ArrowRight size={16} />
                  </a>
                </>
              )
            )}
          </section>
          {(!account.profile.program || !account.profile.skills?.length) && (
            <a className="profile-invitation" href={href("profile")}>
              <ThinkIcon name="profile" size={29} />
              <div>
                <strong>Make it more you</strong>
                <p>Add your course and skills for more relevant suggestions.</p>
                <span>
                  Complete your profile <ArrowRight size={15} />
                </span>
              </div>
            </a>
          )}
          <a className="guidance-invitation" href={href("assistant")}>
            <Artwork kind="learning" />
            <div>
              <h2>A question before you apply?</h2>
              <p>Find preparation advice in approved learning resources.</p>
              <strong>
                Explore guidance <ArrowRight size={15} />
              </strong>
            </div>
          </a>
        </aside>
      </div>
    </div>
  );
}
