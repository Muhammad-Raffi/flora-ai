const burger = document.querySelector("[data-burger]");
const mobileNav = document.querySelector("[data-mobile-nav]");

if (burger && mobileNav) {
  burger.addEventListener("click", () => {
    const isOpen = burger.getAttribute("aria-expanded") === "true";
    burger.setAttribute("aria-expanded", String(!isOpen));
    burger.setAttribute("aria-label", isOpen ? "Buka menu" : "Tutup menu");
    mobileNav.hidden = isOpen;
  });
}

const form = document.querySelector("[data-recommendation-form]");

if (form) {
  const steps = Array.from(form.querySelectorAll("[data-step]"));
  const progress = form.querySelector("[data-progress-bar]");
  const stepCount = form.querySelector("[data-step-count]");
  const stageActions = form.querySelector(".stage-actions");
  const prevButton = form.querySelector("[data-prev-step]");
  const errorText = form.querySelector("[data-step-error]");
  const autoAdvanceDelay = 220;
  let activeStep = Math.max(0, steps.findIndex((step) => !step.querySelector("input:checked")));
  let autoAdvanceTimer = 0;

  if (activeStep < 0) {
    activeStep = steps.length - 1;
  }

  const showError = (message) => {
    if (!errorText) return;
    errorText.textContent = message;
    errorText.hidden = false;
  };

  const hideError = () => {
    if (!errorText) return;
    errorText.hidden = true;
  };

  const currentStepAnswered = () => Boolean(steps[activeStep]?.querySelector("input:checked"));

  const setAutoAdvancing = (isAdvancing) => {
    form.classList.toggle("is-auto-advancing", isAdvancing);
  };

  const renderStep = ({ focusQuestion = false } = {}) => {
    steps.forEach((step, index) => {
      const isActive = index === activeStep;
      step.hidden = !isActive;
      step.setAttribute("aria-hidden", String(!isActive));
    });

    const current = activeStep + 1;
    const total = steps.length;
    if (stepCount) stepCount.textContent = String(current);
    if (progress) progress.style.width = `${(current / total) * 100}%`;

    if (prevButton) prevButton.hidden = activeStep === 0;
    if (stageActions) stageActions.hidden = activeStep === 0;
    hideError();

    if (focusQuestion) {
      const legend = steps[activeStep]?.querySelector("legend");
      legend?.focus({ preventScroll: true });
    }
  };

  const moveToStep = (stepIndex) => {
    activeStep = Math.max(0, Math.min(stepIndex, steps.length - 1));
    renderStep({ focusQuestion: true });
  };

  const advanceFromChoice = () => {
    window.clearTimeout(autoAdvanceTimer);
    if (!currentStepAnswered()) return;

    setAutoAdvancing(true);
    autoAdvanceTimer = window.setTimeout(() => {
      setAutoAdvancing(false);
      if (activeStep === steps.length - 1) {
        form.requestSubmit();
        return;
      }

      moveToStep(activeStep + 1);
    }, autoAdvanceDelay);
  };

  prevButton?.addEventListener("click", () => {
    window.clearTimeout(autoAdvanceTimer);
    setAutoAdvancing(false);
    moveToStep(activeStep - 1);
  });

  form.addEventListener("change", (event) => {
    hideError();
    const target = event.target;
    if (!(target instanceof HTMLInputElement) || target.type !== "radio") return;
    if (!steps[activeStep]?.contains(target)) return;
    advanceFromChoice();
  });

  form.addEventListener("submit", (event) => {
    const unansweredIndex = steps.findIndex((step) => !step.querySelector("input:checked"));
    if (unansweredIndex !== -1) {
      event.preventDefault();
      window.clearTimeout(autoAdvanceTimer);
      setAutoAdvancing(false);
      activeStep = unansweredIndex;
      renderStep({ focusQuestion: true });
      showError("Masih ada pilihan yang belum diisi.");
    }
  });

  renderStep();
}