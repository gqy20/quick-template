const statusRegion = document.querySelector(".copy-status");
let statusTimer;

function showStatus(message) {
  if (!statusRegion) return;
  window.clearTimeout(statusTimer);
  statusRegion.textContent = message;
  statusRegion.classList.add("is-visible");
  statusTimer = window.setTimeout(() => {
    statusRegion.classList.remove("is-visible");
  }, 1800);
}

async function copyText(value) {
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(value);
      return;
    } catch {
      // Browser permissions can reject the modern API; use the local fallback.
    }
  }

  const textarea = document.createElement("textarea");
  textarea.value = value;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.append(textarea);
  textarea.select();
  const copied = document.execCommand("copy");
  textarea.remove();
  if (!copied) throw new Error("copy command was rejected");
}

document.querySelectorAll("[data-copy]").forEach((button) => {
  button.addEventListener("click", async () => {
    const value = button.dataset.copy;
    if (!value) return;

    const previousLabel = button.textContent;
    button.disabled = true;
    try {
      await copyText(value);
      button.textContent = "已复制";
      showStatus("安装命令已复制");
    } catch {
      button.textContent = "复制失败";
      showStatus("无法自动复制，请手动选择命令");
    } finally {
      window.setTimeout(() => {
        button.textContent = previousLabel;
        button.disabled = false;
      }, 1600);
    }
  });
});
