/**
 * Chrome Extension Manifest V3 TypeScript definitions
 */

declare namespace chrome {
  namespace runtime {
    export interface MessageSender {
      id?: string;
      url?: string;
      tab?: chrome.tabs.Tab;
      frameId?: number;
    }

    export const id: string;
    export const lastError: { message?: string } | undefined;

    export function getURL(path: string): string;
    export function sendMessage(
      message: any,
      responseCallback?: (response: any) => void
    ): Promise<any>;
    export function sendMessage(
      extensionId: string,
      message: any,
      responseCallback?: (response: any) => void
    ): Promise<any>;

    export interface ExtensionMessageEvent {
      addListener(
        callback: (
          message: any,
          sender: MessageSender,
          sendResponse: (response?: any) => void
        ) => boolean | void | Promise<any>
      ): void;
      removeListener(callback: (...args: any[]) => void): void;
      hasListener(callback: (...args: any[]) => void): boolean;
    }

    export const onMessage: ExtensionMessageEvent;

    export interface InstalledDetails {
      reason: "install" | "update" | "chrome_update" | "shared_module_update";
      previousVersion?: string;
    }

    export const onInstalled: {
      addListener(callback: (details: InstalledDetails) => void): void;
    };
  }

  namespace tabs {
    export interface Tab {
      id?: number;
      index: number;
      windowId: number;
      highlighted: boolean;
      active: boolean;
      pinned: boolean;
      url?: string;
      title?: string;
      favIconUrl?: string;
      status?: string;
      incognito: boolean;
      width?: number;
      height?: number;
    }

    export interface QueryInfo {
      active?: boolean;
      currentWindow?: boolean;
      url?: string | string[];
      title?: string;
      windowId?: number;
    }

    export function query(queryInfo: QueryInfo): Promise<Tab[]>;
    export function sendMessage(
      tabId: number,
      message: any,
      options?: { frameId?: number }
    ): Promise<any>;
    export function create(createProperties: {
      url?: string;
      active?: boolean;
    }): Promise<Tab>;
  }

  namespace storage {
    export interface StorageArea {
      get(keys?: string | string[] | { [key: string]: any } | null): Promise<{ [key: string]: any }>;
      set(items: { [key: string]: any }): Promise<void>;
      remove(keys: string | string[]): Promise<void>;
      clear(): Promise<void>;
    }

    export const local: StorageArea;
    export const session: StorageArea;
    export const sync: StorageArea;
  }

  namespace sidePanel {
    export interface OpenOptions {
      tabId?: number;
      windowId?: number;
    }

    export interface PanelBehavior {
      openPanelOnActionClick?: boolean;
    }

    export interface PanelOptions {
      tabId?: number;
      path?: string;
      enabled?: boolean;
    }

    export function open(options: OpenOptions): Promise<void>;
    export function setPanelBehavior(behavior: PanelBehavior): Promise<void>;
    export function setOptions(options: PanelOptions): Promise<void>;
  }

  namespace contextMenus {
    export type ContextType =
      | "all"
      | "page"
      | "frame"
      | "selection"
      | "link"
      | "editable"
      | "image"
      | "video"
      | "audio"
      | "launcher"
      | "browser_action"
      | "page_action"
      | "action";

    export interface CreateProperties {
      id?: string;
      title?: string;
      contexts?: ContextType[];
      onclick?: (info: OnClickData, tab?: chrome.tabs.Tab) => void;
      parentId?: string | number;
      type?: "normal" | "checkbox" | "radio" | "separator";
    }

    export interface OnClickData {
      menuItemId: string | number;
      parentMenuItemId?: string | number;
      mediaType?: string;
      linkUrl?: string;
      srcUrl?: string;
      pageUrl?: string;
      frameUrl?: string;
      selectionText?: string;
      editable: boolean;
      wasChecked?: boolean;
      checked?: boolean;
    }

    export function create(
      createProperties: CreateProperties,
      callback?: () => void
    ): string | number;
    export function removeAll(): Promise<void>;

    export const onClicked: {
      addListener(callback: (info: OnClickData, tab?: chrome.tabs.Tab) => void): void;
    };
  }

  namespace commands {
    export interface CommandEvent {
      addListener(callback: (command: string, tab?: chrome.tabs.Tab) => void): void;
    }
    export const onCommand: CommandEvent;
  }

  namespace action {
    export interface TabDetails {
      tabId?: number;
    }

    export interface BadgeTextDetails {
      text: string;
      tabId?: number;
    }

    export interface BadgeBackgroundColorDetails {
      color: string | number[];
      tabId?: number;
    }

    export function setBadgeText(details: BadgeTextDetails): Promise<void>;
    export function setBadgeBackgroundColor(details: BadgeBackgroundColorDetails): Promise<void>;
    export function setTitle(details: { title: string; tabId?: number }): Promise<void>;
    export function setIcon(details: { path?: string | { [index: string]: string }; tabId?: number }): Promise<void>;

    export const onClicked: {
      addListener(callback: (tab: chrome.tabs.Tab) => void): void;
    };
  }

  namespace scripting {
    export interface ScriptInjection<T = any> {
      target: {
        tabId: number;
        allFrames?: boolean;
        frameIds?: number[];
      };
      files?: string[];
      func?: (...args: any[]) => T;
      args?: any[];
    }

    export interface InjectionResult<T = any> {
      frameId: number;
      result?: T;
    }

    export function executeScript<T = any>(
      injection: ScriptInjection<T>
    ): Promise<InjectionResult<T>[]>;
  }
}
