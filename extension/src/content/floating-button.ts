import { CapturedJob } from "../common/types";

export class FloatingMatchButton {
  private hostElement: HTMLElement | null = null;
  private shadowRoot: ShadowRoot | null = null;
  private onTriggerCallback: (job: CapturedJob) => void;

  constructor(onTrigger: (job: CapturedJob) => void) {
    this.onTriggerCallback = onTrigger;
  }

  mount(job: CapturedJob) {
    if (this.hostElement) return; // already mounted

    this.hostElement = document.createElement("resumeiq-button-host");
    this.hostElement.style.all = "initial";
    this.hostElement.style.position = "fixed";
    this.hostElement.style.bottom = "24px";
    this.hostElement.style.right = "24px";
    this.hostElement.style.zIndex = "2147483647"; // maximum z-index

    this.shadowRoot = this.hostElement.attachShadow({ mode: "open" });

    const style = document.createElement("style");
    style.textContent = `
      .pill-container {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        box-sizing: border-box;
        display: flex;
        align-items: center;
        gap: 8px;
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        color: #ffffff;
        padding: 10px 18px;
        border-radius: 9999px;
        box-shadow: 0 10px 25px -5px rgba(79, 70, 229, 0.4), 0 8px 10px -6px rgba(79, 70, 229, 0.2);
        cursor: pointer;
        user-select: none;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        border: 1px solid rgba(255, 255, 255, 0.2);
      }
      .pill-container:hover {
        transform: translateY(-2px) scale(1.03);
        box-shadow: 0 15px 30px -5px rgba(79, 70, 229, 0.5), 0 10px 12px -5px rgba(79, 70, 229, 0.3);
      }
      .pill-container:active {
        transform: translateY(0) scale(0.98);
      }
      .icon {
        width: 18px;
        height: 18px;
        flex-shrink: 0;
      }
      .text-wrap {
        display: flex;
        flex-direction: column;
        line-height: 1.2;
      }
      .label {
        font-size: 13px;
        font-weight: 700;
        letter-spacing: -0.01em;
      }
      .subtext {
        font-size: 10px;
        opacity: 0.85;
      }
      .close-btn {
        margin-left: 4px;
        opacity: 0.6;
        cursor: pointer;
        padding: 2px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: opacity 0.15s;
      }
      .close-btn:hover {
        opacity: 1;
        background: rgba(255, 255, 255, 0.2);
      }
      .toast {
        display: none;
        position: absolute;
        bottom: 55px;
        right: 0;
        background: #1e1b4b;
        color: #e0e7ff;
        padding: 8px 14px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 500;
        white-space: nowrap;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      }
    `;

    const container = document.createElement("div");
    container.className = "pill-container";

    container.innerHTML = `
      <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
      </svg>
      <div class="text-wrap">
        <span class="label">Match with ResumeIQ</span>
        <span class="subtext">${job.title ? (job.title.length > 25 ? job.title.slice(0, 22) + "..." : job.title) : "Job Detected"}</span>
      </div>
      <div class="close-btn" title="Dismiss">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </div>
      <div class="toast" id="toast">Opening ResumeIQ Panel...</div>
    `;

    // Click handler for match
    container.addEventListener("click", (e) => {
      const target = e.target as HTMLElement;
      if (target.closest(".close-btn")) {
        e.stopPropagation();
        this.destroy();
        return;
      }

      const toast = this.shadowRoot?.getElementById("toast");
      if (toast) toast.style.display = "block";

      this.onTriggerCallback(job);
    });

    this.shadowRoot.appendChild(style);
    this.shadowRoot.appendChild(container);
    document.body.appendChild(this.hostElement);
  }

  destroy() {
    if (this.hostElement) {
      this.hostElement.remove();
      this.hostElement = null;
      this.shadowRoot = null;
    }
  }
}
