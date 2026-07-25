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
      this.show(decodeParam(error), 'error');
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
      modal.classList.add('active');
    }
  }

  static close(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.remove('active');
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
    }
  }
}

// ============================================================================
// GESTOR DE FORMULARIOS
// ============================================================================

class FormManager {
  static attachLoadingState(formSelector = 'form') {
    document.querySelectorAll(formSelector).forEach(form => {
      form.addEventListener('submit', () => {
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn && !submitBtn.disabled) {
          submitBtn.disabled = true;
          const originalText = submitBtn.textContent;
          submitBtn.setAttribute('data-original-text', originalText);
          submitBtn.innerHTML = `
            <span class="spinner" style="width: 0.875rem; height: 0.875rem; margin-right: 0.5rem; display: inline-block; border: 2px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%;"></span>
            Cargando...
          `;
        }
      });
    });
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
      this.toolbar.style.display = selected.length > 0 ? 'flex' : 'none';
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

document.addEventListener('DOMContentLoaded', () => {
  // Inicializar gestor de temas
  new ThemeManager();

  // Inicializar gestor de toasts
  window.toastManager = new ToastManager();
  window.toastManager.showFromParams();

  // Inicializar gestor de formularios
  FormManager.attachLoadingState();

  // Inicializar gestor de selección múltiple
  window.multiSelectManager = new MultiSelectManager();

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
