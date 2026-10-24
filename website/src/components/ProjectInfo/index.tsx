import type {ReactNode} from 'react';
import Link from '@docusaurus/Link';
import ThemedImage from '@theme/ThemedImage';
import useBaseUrl from '@docusaurus/useBaseUrl';
import {Bug, CloudDownload, Lightbulb, Shapes, Users, createLucideIcon} from 'lucide-react';

import hacs from '@site/../hacs.json';
import manifest from '@site/../custom_components/netzooe_eservice/manifest.json';

import styles from './styles.module.css';

const repository = 'https://github.com/superbox-dev/netzooe_eservice';
// Explanation of the IoT classes in the Home Assistant blog
const iotClasses = 'https://www.home-assistant.io/blog/2016/02/12/classifying-the-internet-of-things/';
const categories = ['Energy', 'Sensor'];

// Lucide 1.0 removed the brand icons, this is the "github" icon of lucide-react 0.577 (ISC license)
const Github = createLucideIcon('github', [
    [
        'path',
        {
            d: 'M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4',
            key: 'tonef',
        },
    ],
    ['path', {d: 'M9 18c-4.51 2-5-2-7-2', key: '9comsn'}],
]);

// "cloud_polling" -> "Cloud Polling", the anchor in the blog is "#cloud-polling"
function iotClass(): {label: string; anchor: string} {
    const words = manifest.iot_class.split('_');
    return {
        label: words.map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join(' '),
        anchor: words.join('-'),
    };
}

// Integration card above the table of contents, styled after the Home Assistant integration sidebar
export default function ProjectInfo(): ReactNode {
    const {label, anchor} = iotClass();

    return (
        <div className={styles.projectInfo}>
            <section className={styles.module}>
                <div className={styles.logo}>
                    <ThemedImage
                        className={styles.brand}
                        alt={manifest.name}
                        sources={{light: useBaseUrl('/logo.png'), dark: useBaseUrl('/dark_logo.png')}}
                        width={891}
                        height={256}
                    />
                    {/* The "My Home Assistant" badge of the integration pages on home-assistant.io */}
                    <Link href={`https://my.home-assistant.io/redirect/config_flow_start/?domain=${manifest.domain}`}>
                        <img
                            src="https://my.home-assistant.io/badges/config_flow_start.svg"
                            alt="Add integration to my Home Assistant"
                            height={37}
                        />
                    </Link>
                    <Link href={`${repository}/releases`}>
                        <img
                            src="https://img.shields.io/github/v/release/superbox-dev/netzooe_eservice?label=Release"
                            alt="Latest release on GitHub"
                            height={20}
                        />
                    </Link>
                </div>
                <p className={styles.section}>
                    A custom integration, installed with <Link href="https://hacs.xyz">HACS</Link>. It requires Home Assistant{' '}
                    {hacs.homeassistant} or newer.
                </p>
                <p className={styles.section}>
                    A community project, not affiliated with or endorsed by Netz Oberösterreich GmbH. Netz OÖ is a trademark of its
                    owner.
                </p>
                <p className={styles.section}>
                    <CloudDownload className={styles.icon} aria-hidden="true" /> Its IoT class is <Link href={`${iotClasses}#${anchor}`}>{label}</Link>.
                </p>
                <p className={styles.section}>
                    <Link href={repository}>
                        <Github className={styles.icon} aria-hidden="true" /> View source on GitHub
                    </Link>
                    <br />
                    <Link href={`${repository}/issues?q=is%3Aissue+is%3Aopen+label%3Abug`}>
                        <Bug className={styles.icon} aria-hidden="true" /> View known issues
                    </Link>
                    <br />
                    <Link href={`${repository}/issues/new/choose`}>
                        <Lightbulb className={styles.icon} aria-hidden="true" /> Request a feature
                    </Link>
                </p>
            </section>
            <section className={styles.module}>
                <h2 className={styles.title}>
                    <Shapes className={styles.icon} aria-hidden="true" /> Categories
                </h2>
                <ul className={styles.list}>
                    {categories.map((category) => (
                        <li key={category}>{category}</li>
                    ))}
                </ul>
            </section>
            <section className={styles.module}>
                <h2 className={styles.title}>
                    <Users className={styles.icon} aria-hidden="true" /> Code owners
                </h2>
                {manifest.codeowners.map((codeowner) => {
                    const user = codeowner.replace(/^@/, '');
                    return (
                        <Link key={user} className={styles.owner} href={`https://github.com/${user}`}>
                            <img
                                src={`https://avatars.githubusercontent.com/${user}?size=96`}
                                alt=""
                                width={32}
                                height={32}
                            />
                            {codeowner}
                        </Link>
                    );
                })}
            </section>
        </div>
    );
}
