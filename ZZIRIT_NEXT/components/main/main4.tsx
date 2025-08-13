"use client"

import Image from "next/image"
import { motion } from "framer-motion"
import DevProcess from "../plusprocess/dev-process"

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.3,
      delayChildren: 0.2,
    },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
}

export default function TeamSection() {
  return (
    <motion.section
      initial="hidden"
      whileInView="visible"
      viewport={{ once: false, amount: 0.5 }}
      variants={containerVariants}
      className="w-full h-full flex flex-col items-center justify-center p-4 sm:p-8"
    >
      <div className="w-full max-w-7xl mx-auto">
        <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-5 gap-8 items-center mb-12">
          <div className="lg:col-span-2">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">Our Team & Process</h2>
            <p className="text-lg text-gray-400">
              PCB 제조 공정의 혁신을 위해 고민하고 개발했습니다. 아이디어
              구상부터 AI 모델 연동, 프론트엔드 구현까지의 여정입니다.
            </p>
          </div>
          <div className="lg:col-span-3 flex justify-center lg:justify-end">
            <div className="relative w-full max-w-lg h-auto rounded-lg overflow-hidden shadow-2xl">
              <Image
                src="/images/team-photo.png"
                alt="PCB-Manager 개발팀"
                width={600}
                height={400}
                className="object-cover"
              />
            </div>
          </div>
        </motion.div>

        <motion.div variants={itemVariants}>
          <DevProcess />
        </motion.div>
      </div>
    </motion.section>
  )
}
