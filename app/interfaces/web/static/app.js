// ============================================================================
// APP.JS - INTERACTIVIDAD GLOBAL
// ============================================================================

/**
 * Sistema completo de interactividad para Book Library Sync
 * Características:
 * - Gestión de tema (claro/oscuro) con localStorage
 * - Sistema de toasts con auto-dismiss
 * - Modales y confirmaciones
 * - Selección múltiple de libros
 * - Loading states en formularios
 */

// ============================================================================
// CONFIGURACIÓN GLOBAL
// ============================================================================

const CONFIG = {
  THEME_STORAGE_KEY: 'book-library-theme',
  TOAST_DURATION: 3500,
  ANIMATION_DURATION: 300,
};

// ============================================================================
// UTILIDADES
// ============================================================================

/**
 * Obtiene el valor de un parámetro de query
 */
function getQueryParam(name) {
  const params = new URLSearchParams(window.location.search);
  return params.get(name);
}

/**
 * Decodifica una cadena URL
 */
function decodeParam(param) {
  try {
    return decodeURIComponent(param);
  } catch {
    return param;
  }
}

/**
 * Espera asincronamente durante un tiempo
 */
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// ============================================================================
// SISTEMA DE TEMA MEJORADO
// ============================================================================

class ThemeManager {
  constructor() {
    this.htmlElement = document.documentElement;
    this.themeToggle = document.getElementById('theme-toggle');
    this.themeIcon = document.getElementById('theme-icon');
    this.init();
  }

  init() {
    this.applyStoredTheme();
    this.attachListeners();
    this.watchSystemTheme();
  }

  applyStoredTheme() {
    let theme = localStorage.getItem(CONFIG.THEME_STORAGE_KEY);

    if (!theme) {
      theme = window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light';
    }

    this.setTheme(theme);
  }

  setTheme(theme) {
    this.htmlElement.setAttribute('data-theme', theme);
    localStorage.setItem(CONFIG.THEME_STORAGE_KEY, theme);
    this.updateIcon(theme);
  }

  updateIcon(theme) {
    if (this.themeIcon) {
      this.themeIcon.textContent = theme === 'dark' ? '☀️' : '🌙';
    }
  }

  toggle() {
    const currentTheme = this.htmlElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    this.setTheme(newTheme);
  }

  attachListeners() {
    if (this.themeToggle) {
      this.themeToggle.addEventListener('click', () => this.toggle());
    }
  }

  watchSystemTheme() {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
      if (!localStorage.getItem(CONFIG.THEME_STORAGE_KEY)) {
        this.setTheme(e.matches ? 'dark' : 'light');
      }
    });
  }
}

// ============================================================================
// SISTEMA DE TOASTS MEJORADO
// ============================================================================

class ToastManager {
  constructor() {
    this.container = document.getElementById('toastContainer');
    if (!this.container) {
      this.createContainer();
    }
  }

  createContainer() {
    this.container = document.createElement('div');
    this.container.id = 'toastContainer';
    this.container.className = 'toast-container';
    document.body.appendChild(this.container);
  }

  show(message, type = 'info', duration = CONFIG.TOAST_DURATION) {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const iconMap = {
      success: '✓',
      error: '✕',
      warning: '⚠',
      info: 'ℹ',
    };

    const icon = iconMap[type] || 'ℹ';

    toast.innerHTML = `
      <span class="toast-icon">${icon}</span>
      <span>${this.escapeHtml(message)}</span>
    `;

    this.container.appendChild(toast);

    setTimeout(() => {
      toast.style.animation = `slideOutRight ${CONFIG.ANIMATION_DURATION}ms ease-in forwards`;
      setTimeout(() => toast.remove(), CONFIG.ANIMATION_DURATION);
    }, duration);
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  showFromParams() {
    const message = getQueryParam('message');
    const error = getQueryParam('error');

    if (message) {
      this.show(decodeParam(message), 'success');
    }
    if (error) {
      window.setTimeout(() => {
        this.show(decodeParam(error), 'error');
      }, 9000);
    }
  }
}

// ============================================================================
// GESTOR DE MODALES
// ============================================================================

class ModalManager {
  static open(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      // The modal HTML uses class="modal-backdrop" with the HTML `hidden`
      // attribute as the default state. We need to clear BOTH for the modal
      // to actually appear: toggle the `active` class (matched by CSS) and
      // remove the `hidden` attribute (otherwise the browser keeps it
      // hidden regardless of any CSS rule).
      modal.removeAttribute('hidden');
      modal.classList.add('active');
      document.body.classList.add('modal-open');
      const focusable = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
      if (focusable) {
        focusable.focus();
      }
    }
  }

  static close(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.remove('active');
      modal.setAttribute('hidden', '');
      document.body.classList.remove('modal-open');
    }
  }

  static closeOnBackdropClick(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.addEventListener('click', e => {
        if (e.target === modal) {
          this.close(modalId);
        }
      });

      modal.addEventListener('keydown', e => {
        if (e.key === 'Escape') {
          this.close(modalId);
        }
      });
    }
  }
}

// ============================================================================
// GESTOR DE FORMULARIOS
// ============================================================================

class FormManager {
  static attachLoadingState(formSelector = 'form') {
    document.querySelectorAll(formSelector).forEach(form => {
      const shouldShowPending = form.dataset.pendingSubmit === 'true' || form.hasAttribute('data-pending-submit');
      form.addEventListener('submit', () => {
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn && !submitBtn.disabled) {
          submitBtn.disabled = true;
          const originalText = submitBtn.textContent;
          submitBtn.setAttribute('data-original-text', originalText);
          submitBtn.innerHTML = `
            <span class="spinner" style="width: 0.875rem; height: 0.875rem; margin-right: 0.5rem; display: inline-block; border: 2px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%;"></span>
            ${shouldShowPending ? 'Pensando...' : 'Cargando...'}
          `;
        }

        if (shouldShowPending) {
          this.showPendingOverlay(form);
        }
      });
    });
  }

  static showPendingOverlay(form) {
    const overlay = document.getElementById('pendingOverlay');
    if (!overlay) return;

    overlay.removeAttribute('hidden');
    const title = overlay.querySelector('.pending-title');
    const subtitle = overlay.querySelector('.pending-subtitle');
    if (title) {
      title.textContent = 'Estamos cargando tu biblioteca...';
    }
    if (subtitle) {
      subtitle.textContent = 'La respuesta puede tardar unos segundos si el servicio está ocupado.';
    }

    if (!window.__pendingOverlayTimer) {
      window.__pendingOverlayTimer = window.setTimeout(() => {
        if (!overlay.hasAttribute('hidden')) {
          if (subtitle) {
            subtitle.textContent = 'Todavía seguimos esperando la respuesta. Espera un momento más.';
          }
        }
      }, 8000);
    }
  }

  static hidePendingOverlay() {
    const overlay = document.getElementById('pendingOverlay');
    if (overlay) {
      overlay.setAttribute('hidden', '');
    }
    if (window.__pendingOverlayTimer) {
      window.clearTimeout(window.__pendingOverlayTimer);
      window.__pendingOverlayTimer = null;
    }
  }
}

// ============================================================================
// GESTOR DE SELECCIÓN MÚLTIPLE (Libros)
// ============================================================================

class MultiSelectManager {
  constructor() {
    this.toolbar = document.getElementById('selection-toolbar');
    this.countElement = document.getElementById('selected-count');
    this.checkboxes = document.querySelectorAll('.book-select');
    
    if (this.checkboxes.length > 0) {
      this.init();
    }
  }

  init() {
    this.checkboxes.forEach(checkbox => {
      checkbox.addEventListener('change', () => this.update());
    });
  }

  update() {
    const selected = document.querySelectorAll('.book-select:checked');
    
    if (this.toolbar) {
      this.toolbar.classList.toggle('is-hidden', selected.length === 0);
    }

    if (this.countElement) {
      this.countElement.textContent = selected.length;
    }
  }

  selectAll() {
    const allChecked = Array.from(this.checkboxes).every(cb => cb.checked);
    this.checkboxes.forEach(cb => {
      cb.checked = !allChecked;
    });
    this.update();
  }

  deleteSelected() {
    const selected = document.querySelectorAll('.book-select:checked');
    
    if (selected.length === 0) {
      if (window.toastManager) {
        window.toastManager.show('Selecciona al menos un libro', 'warning');
      }
      return;
    }

    const confirmDelete = confirm(
      `¿Eliminar ${selected.length} libro(s) seleccionado(s)? Esta acción no se puede deshacer.`
    );

    if (!confirmDelete) return;

    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/web/books/delete-selected';

    selected.forEach(checkbox => {
      const input = document.createElement('input');
      input.type = 'hidden';
      input.name = 'selected_ids';
      input.value = checkbox.value;
      form.appendChild(input);
    });

    document.body.appendChild(form);
    form.submit();
  }

  clearLibrary() {
    const modal = document.getElementById('clearModal');
    if (modal) {
      ModalManager.open('clearModal');
    }
  }
}

// ============================================================================
// INICIALIZACIÓN EN DOCUMENT READY
// ============================================================================

function initializeSearchModeTabs() {
  const tabs = Array.from(document.querySelectorAll('.tab'));
  const form = document.getElementById('search-mode-form');
  const input = document.getElementById('search-query-input');
  const button = document.getElementById('search-submit-button');
  const help = document.getElementById('search-mode-help');

  if (!form || !input || !button || tabs.length === 0) {
    return;
  }

  const modeConfig = {
    local: {
      action: '/web/search/local',
      buttonText: 'Buscar en mi biblioteca',
      placeholder: 'Busca en tu biblioteca...',
      helpText: 'Busca títulos, autores o categorías que ya tienes guardados en tu colección.',
      ariaLabel: 'Buscar en biblioteca',
    },
    google: {
      action: '/web/search/google',
      buttonText: 'Buscar en Google',
      placeholder: 'Busca en Google Books...',
      helpText: 'Consulta Google Books y añade resultados a tu biblioteca en segundos.',
      ariaLabel: 'Buscar en Google Books',
    },
    sync: {
      action: '/web/sync',
      buttonText: 'Sincronizar',
      placeholder: 'Sincroniza una búsqueda personalizada...',
      helpText: 'Importa resultados desde Google Books directamente a tu colección.',
      ariaLabel: 'Sincronizar desde Google Books',
    },
  };

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const mode = tab.dataset.mode;
      const config = modeConfig[mode];
      if (!config) return;

      tabs.forEach(item => {
        const isActive = item === tab;
        item.classList.toggle('active', isActive);
        item.setAttribute('aria-selected', String(isActive));
      });

      form.action = config.action;
      button.textContent = config.buttonText;
      input.placeholder = config.placeholder;
      input.setAttribute('aria-label', config.ariaLabel);
      if (help) {
        help.textContent = config.helpText;
      }
    });
  });
}

function initializeBookSelectionButtons() {
  const toggles = Array.from(document.querySelectorAll('.book-select-toggle'));
  if (toggles.length === 0) return;

  toggles.forEach(toggle => {
    toggle.addEventListener('click', () => {
      const bookId = toggle.dataset.bookId;
      const hiddenCheckbox = document.querySelector(`.book-select[value="${bookId}"]`);

      if (!hiddenCheckbox) {
        return;
      }

      hiddenCheckbox.checked = !hiddenCheckbox.checked;
      toggle.setAttribute('aria-pressed', String(hiddenCheckbox.checked));
      toggle.textContent = hiddenCheckbox.checked ? 'Seleccionado' : 'Seleccionar';

      if (window.multiSelectManager) {
        window.multiSelectManager.update();
      }
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  // Inicializar gestor de temas
  new ThemeManager();
  FormManager.hidePendingOverlay();

  // Inicializar gestor de toasts
  window.toastManager = new ToastManager();
  window.toastManager.showFromParams();

  // Inicializar gestor de formularios
  FormManager.attachLoadingState();

  // Inicializar gestor de selección múltiple
  window.multiSelectManager = new MultiSelectManager();

  // Inicializar tabs de búsqueda
  initializeSearchModeTabs();

  // Inicializar selección de libros desde botones
  initializeBookSelectionButtons();

  // Configurar click exterior para cerrar modales
  ModalManager.closeOnBackdropClick('deleteModal');
  ModalManager.closeOnBackdropClick('clearModal');
});

// ============================================================================
// FUNCIONES GLOBALES PARA TEMPLATES
// ============================================================================

/**
 * Mostrar toast (compatible con template)
 */
window.showToast = function(message, type = 'info') {
  if (window.toastManager) {
    window.toastManager.show(message, type);
  }
};

/**
 * Seleccionar todos los libros
 */
window.selectAllBooks = function() {
  if (window.multiSelectManager) {
    window.multiSelectManager.selectAll();
  }
};

/**
 * Eliminar libros seleccionados
 */
window.deleteSelected = function() {
  if (window.multiSelectManager) {
    window.multiSelectManager.deleteSelected();
  }
};

/**
 * Abrir modal de limpieza
 */
window.clearAllBooks = function() {
  if (window.multiSelectManager) {
    window.multiSelectManager.clearLibrary();
  }
};

/**
 * Cerrar modal de limpieza
 */
window.closeClearModal = function() {
  ModalManager.close('clearModal');
};

/**
 * Cerrar modal de eliminación (usado en detalle)
 */
window.closeDeleteModal = function() {
  ModalManager.close('deleteModal');
};

/**
 * Eliminar libro (usado en detalle)
 */
window.deleteBook = function() {
  const modal = document.getElementById('deleteModal');
  if (modal) {
    ModalManager.open('deleteModal');
  }
};

/**
 * Manejar envío de formulario
 */
window.handleFormSubmit = function(form) {
  const submitBtn = form.querySelector('button[type="submit"]');
  if (submitBtn) {
    submitBtn.disabled = true;
    const originalText = submitBtn.textContent;
    submitBtn.setAttribute('data-original-text', originalText);
    submitBtn.innerHTML = `
      <span class="spinner" style="width: 0.875rem; height: 0.875rem; margin-right: 0.5rem; display: inline-block; border: 2px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%;"></span>
      ${originalText === 'Confirmar limpieza' ? 'Limpiando...' : 'Cargando...'}
    `;
  }
  return true;
};
